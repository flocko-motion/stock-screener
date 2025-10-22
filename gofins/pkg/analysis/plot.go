package analysis

import (
	"fmt"
	"image/color"
	"math"
	"os"
	"path/filepath"
	"time"

	"github.com/flocko-motion/gofins/pkg/types"
	"gonum.org/v1/gonum/stat/distuv"
	"gonum.org/v1/plot"
	"gonum.org/v1/plot/plotter"
	"gonum.org/v1/plot/vg"
	"gonum.org/v1/plot/vg/draw"
)

const growthLineMax = 0.5

// ChartOptions contains all options for creating a price chart
type ChartOptions struct {
	TimeFrom   time.Time
	TimeTo     time.Time
	Ticker     string
	Prices     []types.PriceData
	Stats      Stats
	OutputPath string
	LimitY     bool // When false, doesn't limit y-values
}

// PlotChart creates a price chart with proper axis formatting
func PlotChart(opts ChartOptions) error {
	if err := os.MkdirAll(filepath.Dir(opts.OutputPath), 0755); err != nil {
		return err
	}

	priceChart, err := createPriceChart(opts)
	if err != nil {
		return err
	}

	// Save the plot
	const width = 8 * vg.Inch
	const height = 6 * vg.Inch

	return priceChart.Save(width, height, opts.OutputPath)
}

// PlotHistogram creates a separate histogram chart
func PlotHistogram(ticker string, stats Stats, outputPath string) error {
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return err
	}

	histChart, err := createHistogramChart(ticker, stats)
	if err != nil {
		return err
	}

	// Save the plot
	const width = 6 * vg.Inch
	const height = 4 * vg.Inch

	return histChart.Save(width, height, outputPath)
}

func createPriceChart(opts ChartOptions) (*plot.Plot, error) {
	p := plot.New()
	p.Title.Text = fmt.Sprintf("%s - Normalized Price (Log Scale)", opts.Ticker)
	p.X.Label.Text = "Year"
	p.Y.Label.Text = "Price"

	if len(opts.Prices) == 0 {
		return p, nil
	}

	// Set up log scale
	p.Y.Scale = plot.LogScale{}

	// Set fixed range only if limitY is true
	if opts.LimitY {
		p.Y.Min = 1
		yearsElapsed := float64(opts.TimeTo.Unix()-opts.TimeFrom.Unix()) / (365.25 * 24 * 3600)
		p.Y.Max = math.Pow(1.0+growthLineMax, yearsElapsed)
	}

	// Custom tick formatter for Y-axis (log scale)
	p.Y.Tick.Marker = &logTickFormatter{}

	// Custom tick formatter for X-axis (dates)
	p.X.Tick.Marker = &dateTickFormatter{prices: opts.Prices}

	// Add year-based background colors FIRST (so they appear in background)
	addYearBackgrounds(p, opts.Prices)

	// Add grid
	p.Add(plotter.NewGrid())

	// Normalize prices to start at 1.0
	firstPrice := opts.Prices[0].Close
	pts := make(plotter.XYs, len(opts.Prices))

	iWrite := 0
	for _, price := range opts.Prices {
		normalizedPrice := price.Close / firstPrice

		// Clip values to our Y-axis range only if limitY is true
		if opts.LimitY {
			if normalizedPrice < p.Y.Min {
				pts[iWrite].Y = p.Y.Min
			} else if normalizedPrice > p.Y.Max {
				pts[iWrite].Y = p.Y.Max
			} else {
				pts[iWrite].Y = normalizedPrice
			}
		} else {
			pts[iWrite].Y = normalizedPrice
		}

		pts[iWrite].X = float64(price.Date.Unix())
		iWrite++
	}
	pts = pts[0:iWrite]

	line, err := plotter.NewLine(pts)
	if err != nil {
		return nil, err
	}

	line.Color = color.RGBA{R: 0, G: 0, B: 0, A: 255}
	line.Width = vg.Points(1.5)

	p.Add(line)

	// Add constant growth lines
	addGrowthLines(p, opts)

	return p, nil
}

func addYearBackgrounds(p *plot.Plot, prices []types.PriceData) {
	if len(prices) == 0 {
		return
	}

	// Group prices by year and find the last price of each year
	yearData := make(map[int][]types.PriceData)
	for _, price := range prices {
		year := price.Date.Year()
		yearData[year] = append(yearData[year], price)
	}

	// Sort years
	var years []int
	for year := range yearData {
		years = append(years, year)
	}

	// Simple sort
	for i := 0; i < len(years)-1; i++ {
		for j := i + 1; j < len(years); j++ {
			if years[i] > years[j] {
				years[i], years[j] = years[j], years[i]
			}
		}
	}

	for i, year := range years {
		// Calculate year start and end times
		yearStart := time.Date(year, 1, 1, 0, 0, 0, 0, time.UTC)
		var yearEnd time.Time
		if i+1 < len(years) {
			yearEnd = time.Date(years[i+1], 1, 1, 0, 0, 0, 0, time.UTC)
		} else {
			// For the last year, use the last data point
			yearEnd = prices[len(prices)-1].Date
		}

		// Find the last price of this year
		yearPrices := yearData[year]
		if len(yearPrices) == 0 {
			continue
		}

		// Sort prices by date to find the last one
		lastPrice := yearPrices[0]
		for _, price := range yearPrices {
			if price.Date.After(lastPrice.Date) {
				lastPrice = price
			}
		}

		// Find the price from one year ago (or closest available)
		var yearAgoPrice *types.PriceData

		// Look for the closest price to one year ago
		minDiff := time.Duration(365 * 24 * time.Hour) // Max difference
		for _, price := range prices {
			if price.Date.Before(lastPrice.Date) {
				diff := lastPrice.Date.Sub(price.Date)
				if diff <= minDiff && diff >= time.Duration(300*24*time.Hour) { // At least 300 days
					minDiff = diff
					yearAgoPrice = &price
				}
			}
		}

		// Calculate YoY percentage if we have both prices
		var yoyPercentage float64
		if yearAgoPrice != nil {
			yoyPercentage = ((lastPrice.Close - yearAgoPrice.Close) / yearAgoPrice.Close) * 100
		}

		// Create shaded region with color based on YoY percentage
		region := ShadedRegion{
			StartX: float64(yearStart.Unix()),
			EndX:   float64(yearEnd.Unix()),
			Color:  percentageToColor(yoyPercentage, 0.95), // Very light background
		}
		if i == 0 {
			region.StartX = float64(prices[0].Date.Unix())
		}
		p.Add(region)

	}
}

// ShadedRegion represents a vertical shaded area on the plot
type ShadedRegion struct {
	StartX float64
	EndX   float64
	Color  color.Color
}

// Plot implements the plot.Plotter interface, drawing the shaded region
func (s ShadedRegion) Plot(c draw.Canvas, plt *plot.Plot) {
	// Get the plot's coordinate system
	xMin, xMax := plt.X.Min, plt.X.Max
	yMin, yMax := plt.Y.Min, plt.Y.Max

	// Convert data coordinates to canvas coordinates (0-1 normalized)
	x1 := (s.StartX - xMin) / (xMax - xMin)
	x2 := (s.EndX - xMin) / (xMax - xMin)
	y1 := (yMin - yMin) / (yMax - yMin) // Always 0
	y2 := (yMax - yMin) / (yMax - yMin) // Always 1

	// Convert to actual canvas coordinates
	canvasX1 := c.X(x1)
	canvasX2 := c.X(x2)
	canvasY1 := c.Y(y1)
	canvasY2 := c.Y(y2)

	// Create a rectangle representing the shaded area
	rect := vg.Rectangle{
		Min: vg.Point{X: canvasX1, Y: canvasY1},
		Max: vg.Point{X: canvasX2, Y: canvasY2},
	}

	// Fill the rectangle with the specified color
	c.SetColor(s.Color)
	c.Fill(rect.Path())
}

// percentageToColor converts a percentage float to an RGBA color using HSL
// <=0% is red, 0-30% is red to cyan gradient, >30% is cyan
func percentageToColor(percentage float64, lightness float64) color.RGBA {
	var hue float64

	const (
		lowerBound float64 = 0
		upperBound float64 = 50
	)
	switch {
	case percentage <= lowerBound:
		hue = 0 // Red
	case percentage <= upperBound:
		// Linear interpolation from red (0) to cyan (180)
		hue = (percentage / upperBound) * 180
	default:
		hue = 180 // Cyan (same as 30%)
	}

	// Convert HSL to RGB
	// Using fixed saturation (70%) and lightness (50%) for good visibility
	saturation := 1.0

	return hslToRgba(hue, saturation, lightness, 255)
}

// hslToRgba converts HSL color space to RGBA
func hslToRgba(h, s, l float64, alpha uint8) color.RGBA {
	// Normalize hue to 0-360 range
	h = math.Mod(h, 360)
	if h < 0 {
		h += 360
	}

	var r, g, b float64

	if s == 0 {
		// Grayscale
		r, g, b = l, l, l
	} else {
		var c, x, m float64
		c = (1 - math.Abs(2*l-1)) * s
		x = c * (1 - math.Abs(math.Mod(h/60, 2)-1))
		m = l - c/2

		switch {
		case h < 60:
			r, g, b = c, x, 0
		case h < 120:
			r, g, b = x, c, 0
		case h < 180:
			r, g, b = 0, c, x
		case h < 240:
			r, g, b = 0, x, c
		case h < 300:
			r, g, b = x, 0, c
		default:
			r, g, b = c, 0, x
		}

		r += m
		g += m
		b += m
	}

	return color.RGBA{
		R: uint8(math.Round(r * 255)),
		G: uint8(math.Round(g * 255)),
		B: uint8(math.Round(b * 255)),
		A: alpha,
	}
}

func createHistogramChart(ticker string, stats Stats) (*plot.Plot, error) {
	p := plot.New()
	p.Title.Text = fmt.Sprintf("%s - YoY Distribution", ticker)
	p.X.Label.Text = "YoY %"
	p.Y.Label.Text = "Density"

	if len(stats.Histogram) == 0 {
		return p, nil
	}

	// Convert histogram bins to raw data points for plotter.NewHist
	var values plotter.Values
	for _, bin := range stats.Histogram {
		// Add each data point in this bin (represented by bin center)
		binCenter := (bin.Min + bin.Max) / 2
		for i := 0; i < bin.Count; i++ {
			values = append(values, binCenter)
		}
	}

	// Create proper histogram using plotter.NewHist with fewer bins to reduce gaps
	hist, err := plotter.NewHist(values, len(stats.Histogram)/2) // Fewer bins = less gaps
	if err != nil {
		return nil, err
	}

	// Normalize the histogram to sum to one
	hist.Normalize(1)

	// Style the histogram with color based on mean performance
	meanColor := percentageToColor(stats.Mean, 0.4)
	hist.Color = meanColor
	hist.FillColor = meanColor
	hist.LineStyle.Width = vg.Points(0) // No outline
	p.Add(hist)

	// Add normal distribution curve
	normalDist := distuv.Normal{
		Mu:    stats.Mean,
		Sigma: stats.StdDev,
	}
	normalFunc := plotter.NewFunction(normalDist.Prob)
	normalFunc.Color = percentageToColor(stats.Mean, 0.1)
	normalFunc.Width = vg.Points(2)
	p.Add(normalFunc)

	// Set X-axis range based on histogram bounds
	if len(stats.Histogram) > 0 {
		p.X.Min = stats.Histogram[0].Min
		p.X.Max = stats.Histogram[len(stats.Histogram)-1].Max
	}

	// Custom X-axis tick formatter for cleaner labels
	p.X.Tick.Marker = &histogramTickFormatter{stats.Histogram}

	// Add grid
	p.Add(plotter.NewGrid())

	// Add vertical lines for mean and stddev
	if stats.Mean >= p.X.Min && stats.Mean <= p.X.Max {
		addVerticalLineWithLabel(p, stats.Mean, percentageToColor(stats.Mean, 0.2), fmt.Sprintf("%.1f%%", stats.Mean), vg.Points(5)) // Thicker mean line with value
	}
	for _, i := range []float64{-1, +1} {
		x := stats.Mean + (stats.StdDev * i)
		if x < p.X.Min || x > p.X.Max {
			continue
		}
		addVerticalLineWithLabel(p, x, color.RGBA{R: 80, G: 80, B: 80, A: 255}, fmt.Sprintf("%.1f%%", x), vg.Points(3))
	}
	addVerticalLineWithDashes(p, 0, color.RGBA{R: 0, G: 0, B: 0, A: 255}, "Zero", vg.Points(2), nil) // Black solid line at x=0

	return p, nil
}

func addVerticalLine(p *plot.Plot, x float64, col color.Color, label string, width vg.Length) {
	addVerticalLineWithDashes(p, x, col, label, width, []vg.Length{vg.Points(3), vg.Points(2)})
}

func addVerticalLineWithLabel(p *plot.Plot, x float64, col color.Color, labelText string, width vg.Length) {
	// Add the vertical line
	addVerticalLineWithDashes(p, x, col, labelText, width, []vg.Length{vg.Points(3), vg.Points(2)})

	// Add text label at the top of the line with larger font
	ymax := p.Y.Max
	labels, err := plotter.NewLabels(plotter.XYLabels{
		XYs:    []plotter.XY{{X: x, Y: ymax * 0.95}},
		Labels: []string{labelText},
	})
	if err != nil {
		return
	}

	// Use default text style to avoid nil pointer issues

	p.Add(labels)
}

func addVerticalLineWithDashes(p *plot.Plot, x float64, col color.Color, label string, width vg.Length, dashes []vg.Length) {
	// Get plot bounds to create vertical line
	ymin, ymax := p.Y.Min, p.Y.Max

	// Create line points for vertical line
	pts := make(plotter.XYs, 2)
	pts[0].X = x
	pts[0].Y = ymin
	pts[1].X = x
	pts[1].Y = ymax

	line, err := plotter.NewLine(pts)
	if err != nil {
		return
	}

	line.Color = col
	line.Width = width
	line.LineStyle.Dashes = dashes

	p.Add(line)
}

func addGrowthLines(p *plot.Plot, opts ChartOptions) {
	if len(opts.Prices) == 0 {
		return
	}

	startTime := float64(opts.TimeFrom.Unix())

	// Growth rates with their colors using the HSL color function
	lightness := 0.4
	growthConfig := map[float64]color.Color{}
	for i := float64(0.05); i <= growthLineMax; i += 0.05 {
		growthConfig[i] = percentageToColor(i*100, lightness)
	}

	for rate, col := range growthConfig {
		// Calculate exponential growth: value = 1 * (1 + rate)^years
		// For each time point, calculate years elapsed since start
		pts := make(plotter.XYs, len(opts.Prices))

		ptsCounter := 0
		for _, price := range opts.Prices {
			currentTime := float64(price.Date.Unix())
			yearsElapsed := (currentTime - startTime) / (365.25 * 24 * 3600) // Convert seconds to years
			growthValue := math.Pow(1+rate, yearsElapsed)

			if growthValue > p.Y.Max {
				continue
			}
			pts[ptsCounter].X = currentTime
			pts[ptsCounter].Y = growthValue
			ptsCounter++
		}
		pts = pts[0:ptsCounter]

		if len(pts) == 0 {
			continue
		}
		line, err := plotter.NewLine(pts)
		if err != nil {
			continue
		}

		line.Color = col
		line.Width = vg.Points(2)
		line.LineStyle.Dashes = []vg.Length{vg.Points(2), vg.Points(2)} // Dashed lines

		p.Add(line)

		// Add label for this growth line
		addGrowthLabel(p, rate, pts[len(pts)-1])
	}
}

func addGrowthLabel(p *plot.Plot, rate float64, endPoint plotter.XY) {
	// Create text annotation at the end of the growth line
	label := fmt.Sprintf("%.0f%%", rate*100)

	// Position the label slightly offset from the end point
	x := endPoint.X
	y := endPoint.Y * 1.02 // Slight vertical offset above the line

	labels, err := plotter.NewLabels(plotter.XYLabels{
		XYs:    []plotter.XY{{X: x, Y: y}},
		Labels: []string{label},
	})
	if err != nil {
		return
	}

	p.Add(labels)
}

// Custom tick formatters
type logTickFormatter struct{}

func (l *logTickFormatter) Ticks(min, max float64) []plot.Tick {
	var ticks []plot.Tick

	// Generate ticks at powers of 10
	minExp := math.Floor(math.Log10(min))
	maxExp := math.Ceil(math.Log10(max))

	for exp := minExp; exp <= maxExp; exp++ {
		value := math.Pow(10, exp)
		if value >= min && value <= max {
			// Format labels properly for fractional values
			var label string
			if value >= 1 {
				label = fmt.Sprintf("%.0f", value)
			} else {
				label = fmt.Sprintf("%.1f", value)
			}
			ticks = append(ticks, plot.Tick{
				Value: value,
				Label: label,
			})
		}
	}

	// Add many more intermediate ticks for finer grid
	for exp := minExp; exp <= maxExp; exp++ {
		for _, mult := range []float64{1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 7, 8, 9} {
			value := mult * math.Pow(10, exp)
			if value >= min && value <= max && value >= 1 {
				var label string
				if value < 10 {
					label = fmt.Sprintf("%.1f", value)
				} else {
					label = fmt.Sprintf("%.0f", value)
				}
				ticks = append(ticks, plot.Tick{
					Value: value,
					Label: label,
				})
			}
		}
	}

	// If too many ticks, only show labels for every nth tick
	if len(ticks) > 15 {
		step := len(ticks) / 20
		if step == 0 {
			step = 1
		}
		for i := range ticks {
			if i%step != 0 {
				ticks[i].Label = "" // Keep tick mark but remove label
			}
		}
	}

	return ticks
}

type dateTickFormatter struct {
	prices []types.PriceData
}

func (d *dateTickFormatter) Ticks(min, max float64) []plot.Tick {
	if len(d.prices) == 0 {
		return nil
	}

	var ticks []plot.Tick

	// Find year boundaries in the data
	seenYears := make(map[int]bool)
	for _, price := range d.prices {
		year := price.Date.Year()
		if !seenYears[year] {
			seenYears[year] = true
			// Create tick at start of year
			yearStart := time.Date(year, 1, 1, 0, 0, 0, 0, time.UTC)
			yearUnix := float64(yearStart.Unix())

			if yearUnix >= min && yearUnix <= max {
				ticks = append(ticks, plot.Tick{
					Value: yearUnix,
					Label: fmt.Sprintf("%d", year),
				})
			}
		}
	}

	// If too many year labels, only show every nth year
	if len(ticks) > 15 {
		step := (len(ticks) + 9) / 20 // Show ~10 labels, round up
		for i := range ticks {
			if i%step != 0 {
				ticks[i].Label = "" // Keep tick mark but remove label
			}
		}
	}

	return ticks
}

type histogramTickFormatter struct {
	histogram []HistogramBin
}

func (h *histogramTickFormatter) Ticks(min, max float64) []plot.Tick {
	if len(h.histogram) == 0 {
		return nil
	}

	var ticks []plot.Tick

	// Create ticks at reasonable intervals - every 10% or 20%
	interval := 20.0
	if max-min < 100 {
		interval = 10.0
	}
	if max-min < 50 {
		interval = 5.0
	}

	// Start from a nice round number
	start := math.Floor(min/interval) * interval
	if start < min {
		start += interval
	}

	for value := start; value <= max; value += interval {
		ticks = append(ticks, plot.Tick{
			Value: value,
			Label: fmt.Sprintf("%.0f", value),
		})
	}

	return ticks
}
