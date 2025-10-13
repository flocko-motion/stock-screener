# FINS REST API

## Analysis Endpoints

### List all analyses
```
GET /api/analyses
```
Returns: Array of analysis packages

### Create new analysis
```
POST /api/analyses
Content-Type: application/json

{
  "name": "Analysis Name",
  "interval": "weekly",           // optional, default: "weekly"
  "time_from": "2009",            // optional, default: "2009"
  "time_to": "2024-12-01",        // optional, default: first of current month
  "hist_bins": 100,               // optional, default: 100
  "hist_min": -80.0,              // optional, default: -80.0
  "hist_max": 80.0,               // optional, default: 80.0
  "mcap_min": "100M",             // optional, default: "100M"
  "inception_max": "2020-01-01"   // optional
}
```
Returns: `{ "package_id": "...", "status": "processing" }`

### Get single analysis
```
GET /api/analysis/{id}
```
Returns: Single analysis package

### Update analysis (rename)
```
PUT /api/analysis/{id}
Content-Type: application/json

{
  "name": "New Analysis Name"
}
```
Returns: Updated analysis package

### Delete analysis
```
DELETE /api/analysis/{id}
```
Returns: 204 No Content

### Get analysis results
```
GET /api/analysis/{id}/results
```
Returns: Array of analysis results for the package

### Get analysis chart
```
GET /api/analysis/{id}/chart/{ticker}
```
Returns: PNG image of the chart for the specified ticker

### Get analysis histogram
```
GET /api/analysis/{id}/histogram/{ticker}
```
Returns: PNG image of the histogram for the specified ticker

## Response Format

Analysis response is `db.AnalysisPackage`:
```json
{
  "ID": "uuid",
  "Name": "Analysis Name",
  "CreatedAt": "2024-12-15T10:30:00Z",
  "Interval": "weekly",
  "TimeFrom": "2009-01-01T00:00:00Z",
  "TimeTo": "2024-12-01T00:00:00Z",
  "HistBins": 100,
  "HistMin": -80.0,
  "HistMax": 80.0,
  "McapMin": 100000000,
  "InceptionMax": "2020-01-01T00:00:00Z",
  "SymbolCount": 156,
  "Status": "ready" | "processing" | "failed"
}
```

Analysis result response is an array of `db.AnalysisResult`:
```json
[{
  "inception": "2010-06-29T00:00:00Z",
  "symbol": "AAPL",
  "mean": 12.5,
  "stddev": 8.3,
  "min": -15.2,
  "max": 35.8
}]
```

