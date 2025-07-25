/**
 * Converts ANSI escape codes to HTML with color styling
 * @param {string} text - Text containing ANSI escape codes
 * @returns {string} HTML string with color spans
 */
export function convertAnsiToHtml(text) {
  const colors = {
    '30': '#000000', // black
    '31': '#ff0000', // red
    '32': '#00ff00', // green
    '33': '#ffff00', // yellow
    '34': '#0000ff', // blue
    '35': '#ff00ff', // magenta
    '36': '#00ffff', // cyan
    '37': '#ffffff', // white
    '90': '#808080', // bright black
    '91': '#ff8080', // bright red
    '92': '#80ff80', // bright green
    '93': '#ffff80', // bright yellow
    '94': '#8080ff', // bright blue
    '95': '#ff80ff', // bright magenta
    '96': '#80ffff', // bright cyan
    '97': '#ffffff', // bright white
  }
  
  let result = ''
  let currentColor = ''
  let inEscape = false
  let escapeCode = ''
  
  for (let i = 0; i < text.length; i++) {
    const char = text[i]
    
    if (char === '\x1b' && text[i + 1] === '[') {
      inEscape = true
      escapeCode = ''
      i++ // skip the [
      continue
    }
    
    if (inEscape) {
      if (char === 'm') {
        inEscape = false
        // Parse the escape code
        const codes = escapeCode.split(';')
        for (const code of codes) {
          if (code === '0') {
            currentColor = ''
          } else if (colors[code]) {
            currentColor = colors[code]
          }
        }
      } else {
        escapeCode += char
      }
      continue
    }
    
    if (currentColor) {
      result += `<span style="color: ${currentColor}">${char}</span>`
    } else {
      result += char
    }
  }
  
  return result
} 