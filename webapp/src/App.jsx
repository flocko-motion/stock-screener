import React, { useState, useRef, useEffect } from 'react'
import { useReactTable, getCoreRowModel, getSortedRowModel, getFilteredRowModel, getPaginationRowModel, flexRender, createColumnHelper } from '@tanstack/react-table'
import './App.css'

// ANSI color support
function convertAnsiToHtml(text) {
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
  
  const reset = '\x1b[0m'
  
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

// DataFrameTable component for DataFrameMedia
function DataFrameTable({ schema, data }) {
  const columnHelper = createColumnHelper()
  
  const [columnOrder, setColumnOrder] = useState([])
  const [columnVisibility, setColumnVisibility] = useState({})
  const [columnFilters, setColumnFilters] = useState([])
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: 10,
  })
  const [movingColumnId, setMovingColumnId] = useState(null)
  const [targetColumnId, setTargetColumnId] = useState(null)
  
  // Custom column filter function
  const columnFilterFn = (row, columnId, filterValue) => {
    if (!filterValue) return true
    
    const searchValue = filterValue.toLowerCase()
    const cellValue = String(row.getValue(columnId)).toLowerCase()
    
    // Starts with: ^pattern
    if (searchValue.startsWith('^')) {
      const pattern = searchValue.slice(1)
      return cellValue.startsWith(pattern)
    }
    
    // Ends with: pattern$
    if (searchValue.endsWith('$')) {
      const pattern = searchValue.slice(0, -1)
      return cellValue.endsWith(pattern)
    }
    
    // Greater than or equal: >= number
    if (searchValue.startsWith('>= ')) {
      const numValue = parseFloat(searchValue.slice(3))
      const cellNum = parseFloat(cellValue)
      return !isNaN(cellNum) && cellNum >= numValue
    }
    
    // Less than or equal: <= number
    if (searchValue.startsWith('<= ')) {
      const numValue = parseFloat(searchValue.slice(3))
      const cellNum = parseFloat(cellValue)
      return !isNaN(cellNum) && cellNum <= numValue
    }
    
    // Greater than: > number
    if (searchValue.startsWith('> ')) {
      const numValue = parseFloat(searchValue.slice(2))
      const cellNum = parseFloat(cellValue)
      return !isNaN(cellNum) && cellNum > numValue
    }
    
    // Less than: < number
    if (searchValue.startsWith('< ')) {
      const numValue = parseFloat(searchValue.slice(2))
      const cellNum = parseFloat(cellValue)
      return !isNaN(cellNum) && cellNum < numValue
    }
    
    // Default: contains
    return cellValue.includes(searchValue)
  }
  
  const columns = React.useMemo(
    () =>
      schema.fields
        .filter(field => field.name !== 'index') // Hide the index column
        .map(field => 
          columnHelper.accessor(field.name, {
            header: field.name,
            cell: info => info.getValue(),
            enableSorting: true,
            enableColumnFilter: true,
            enableHiding: true,
            enableResizing: true,
            size: 150,
            minSize: 50,
            maxSize: 500,
            filterFn: columnFilterFn,
          })
        ),
    [schema, columnHelper, columnFilterFn]
  )

  const table = useReactTable({
    data,
    columns,
    state: {
      columnOrder,
      columnVisibility,
      columnFilters,
      pagination,
    },
    onColumnOrderChange: setColumnOrder,
    onColumnVisibilityChange: setColumnVisibility,
    onColumnFiltersChange: setColumnFilters,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    columnResizeMode: 'onChange',
    getRowId: (row) => row.id || row.index,
  })

  // Drag and drop handlers for column reordering
  const handleDragStart = (e, columnId) => {
    setMovingColumnId(columnId)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e, columnId) => {
    e.preventDefault()
    if (movingColumnId && movingColumnId !== columnId) {
      setTargetColumnId(columnId)
    }
  }

  const handleDrop = (e, columnId) => {
    e.preventDefault()
    if (movingColumnId && targetColumnId && movingColumnId !== targetColumnId) {
      const newColumnOrder = [...columnOrder]
      const movingIndex = newColumnOrder.indexOf(movingColumnId)
      const targetIndex = newColumnOrder.indexOf(targetColumnId)
      
      if (movingIndex !== -1 && targetIndex !== -1) {
        newColumnOrder.splice(movingIndex, 1)
        newColumnOrder.splice(targetIndex, 0, movingColumnId)
        setColumnOrder(newColumnOrder)
      }
    }
    setMovingColumnId(null)
    setTargetColumnId(null)
  }

  const handleDragEnd = () => {
    setMovingColumnId(null)
    setTargetColumnId(null)
  }

  return (
    <div className="dataframe-table-wrapper">
      {/* Table Controls Bar */}
      <div className="table-controls">
        <div className="controls-left">
          {/* Pagination controls */}
          <div className="pagination">
            <button onClick={() => table.setPageIndex(0)} disabled={!table.getCanPreviousPage()}>{'<<'}</button>
            <button onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>{'<'}</button>
            <span>
              {table.getState().pagination.pageIndex + 1}/{table.getPageCount()}
              {' '}({table.getFilteredRowModel().rows.length})
            </span>
            <button onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>{'>'}</button>
            <button onClick={() => table.setPageIndex(table.getPageCount() - 1)} disabled={!table.getCanNextPage()}>{'>>'}</button>
            
            {/* Page Size Selector */}
            <div className="page-size-selector">
              <select
                value=""
                onChange={e => {
                  const pageSize = e.target.value === 'ALL' ? (() => {
                    const totalRows = table.getFilteredRowModel().rows.length
                    return totalRows
                  })() : Number(e.target.value)
                  table.setPageSize(pageSize)
                  e.target.value = "" // Reset selection
                }}
              >
                <option value="">Show</option>
                {(() => {
                  const totalRows = table.getFilteredRowModel().rows.length
                  const pageSizeOptions = [10, 100, 1000, totalRows]
                  
                  return pageSizeOptions.map((pageSize, index) => (
                    <option key={`page-size-${pageSize}-${index}`} value={pageSize}>
                      {index === pageSizeOptions.length - 1 ? 'ALL' : pageSize}
                    </option>
                  ))
                })()}
              </select>
            </div>
            
            {/* Column Visibility Dropdown */}
            <div className="column-dropdown">
              <select
                value=""
                onChange={e => {
                  const value = e.target.value
                  if (value === 'show-all') {
                    table.toggleAllColumnsVisible()
                  } else if (value === 'hide-all') {
                    table.toggleAllColumnsVisible()
                  } else if (value) {
                    const column = table.getColumn(value)
                    if (column) {
                      column.toggleVisibility()
                    }
                  }
                  e.target.value = "" // Reset selection
                }}
              >
                <option value="">Columns</option>
                <option value={table.getIsAllColumnsVisible() ? 'hide-all' : 'show-all'}>
                  {table.getIsAllColumnsVisible() ? 'Hide All' : 'Show All'}
                </option>
                <option value="" disabled>──────────</option>
                {table.getAllLeafColumns()
                  .filter(column => column.getCanHide())
                  .map(column => (
                    <option key={column.id} value={column.id}>
                      {column.getIsVisible() ? '✓ ' : '✗ '}{column.id}
                    </option>
                  ))}
              </select>
            </div>
          </div>
        </div>
      </div>
      
      <table className="dataframe-table">
        <thead>
          {table.getHeaderGroups().map(headerGroup => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map(header => (
                <th 
                  key={header.id} 
                  colSpan={header.colSpan}
                  style={{ 
                    width: header.getSize(),
                    position: 'relative'
                  }}
                  draggable
                  onDragStart={(e) => handleDragStart(e, header.column.id)}
                  onDragOver={(e) => handleDragOver(e, header.column.id)}
                  onDrop={(e) => handleDrop(e, header.column.id)}
                  onDragEnd={handleDragEnd}
                  className={`${movingColumnId === header.column.id ? 'dragging' : ''} ${targetColumnId === header.column.id ? 'drag-over' : ''}`}
                >
                  {header.isPlaceholder ? null : (
                    <div className="header-content">
                      <div 
                        className="header-title"
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                        {header.column.getIsSorted() ? (header.column.getIsSorted() === 'desc' ? ' 🔽' : ' 🔼') : ''}
                      </div>
                      {header.column.getCanFilter() && (
                        <input
                          type="text"
                          placeholder={`Filter ${header.column.id}...`}
                          value={header.column.getFilterValue() ?? ''}
                          onChange={e => header.column.setFilterValue(e.target.value)}
                          className="column-filter-input"
                        />
                      )}
                    </div>
                  )}
                  {/* Column Resize Handle */}
                  <div
                    onMouseDown={header.getResizeHandler()}
                    onTouchStart={header.getResizeHandler()}
                    className={`resizer ${header.column.getIsResizing() ? 'isResizing' : ''}`}
                  />
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map(row => (
            <tr key={row.id}>
              {row.getVisibleCells().map(cell => (
                <td 
                  key={cell.id}
                  style={{ width: cell.column.getSize() }}
                >
                  {flexRender(
                    cell.column.columnDef.cell,
                    cell.getContext()
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function App() {
  const [isConnected, setIsConnected] = useState(false)
  const [commandInput, setCommandInput] = useState('')
  const [consoleOutput, setConsoleOutput] = useState([])
  const [tabs, setTabs] = useState([])
  const [activeTab, setActiveTab] = useState(null)
  const [maximizedTab, setMaximizedTab] = useState(null)
  const [sessionId] = useState(Math.floor(Math.random() * 1000000))
  const [mediaHeight, setMediaHeight] = useState(() => window.innerHeight - 200) // Initial height so console is 100px
  
  const commandInputRef = useRef(null)
  const wsRef = useRef(null)
  const isConnectingRef = useRef(false)
  const hasInitializedRef = useRef(false)
  const resizeRef = useRef(null)
  const isResizingRef = useRef(false)
  const consoleOutputRef = useRef(null)
  
  // Command history
  const commandHistoryRef = useRef([])
  const historyIndexRef = useRef(-1)
  const currentInputRef = useRef('')
  
  const addConsoleOutput = (message, type = 'info') => {
    setConsoleOutput(prev => [...prev, { 
      id: Date.now(), 
      message: convertAnsiToHtml(message), 
      type,
      timestamp: new Date() 
    }])
  }
  
  // Auto-scroll console to bottom when new output is added
  useEffect(() => {
    if (consoleOutputRef.current) {
      consoleOutputRef.current.scrollTop = consoleOutputRef.current.scrollHeight
    }
  }, [consoleOutput])
  
  const addToHistory = (command) => {
    if (command.trim() && (commandHistoryRef.current.length === 0 || commandHistoryRef.current[commandHistoryRef.current.length - 1] !== command)) {
      commandHistoryRef.current.push(command)
      if (commandHistoryRef.current.length > 100) {
        commandHistoryRef.current.shift()
      }
    }
    historyIndexRef.current = -1
  }
  
  const navigateHistory = (direction) => {
    if (commandHistoryRef.current.length === 0) return
    
    if (direction === 'up') {
      if (historyIndexRef.current === -1) {
        currentInputRef.current = commandInput
        historyIndexRef.current = commandHistoryRef.current.length - 1
      } else if (historyIndexRef.current > 0) {
        historyIndexRef.current--
      }
    } else if (direction === 'down') {
      if (historyIndexRef.current >= 0) {
        historyIndexRef.current++
        if (historyIndexRef.current >= commandHistoryRef.current.length) {
          historyIndexRef.current = -1
          setCommandInput(currentInputRef.current)
          return
        }
      }
    }
    
    if (historyIndexRef.current >= 0) {
      setCommandInput(commandHistoryRef.current[historyIndexRef.current])
    }
  }
  
  const connectWebSocket = () => {
    if (isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }
    
    isConnectingRef.current = true
    wsRef.current = new WebSocket('ws://localhost:8001')
    
    wsRef.current.onopen = () => {
      setIsConnected(true)
      isConnectingRef.current = false
      addConsoleOutput('Connected', 'success')
      commandInputRef.current?.focus()
    }
    
    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'output') {
          addConsoleOutput(data.content)
        } else if (data.type === 'error') {
          addConsoleOutput(data.content, 'error')
        } else if (data.type === 'media') {
          // Handle media messages - create tabs for each media handle
          console.log('Received media handles:', data.handles)
          data.handles.forEach(handle => {
            // Parse handle format: [type:uuid]
            const match = handle.match(/\[(\w+):([a-f0-9-]+)\]/)
            if (match) {
              const [, mediaType, uuid] = match
              const title = mediaType === 'dataframemedia' ? `DF ${uuid.slice(0, 4)}` : `${mediaType.charAt(0).toUpperCase() + mediaType.slice(1)} ${uuid.slice(0, 8)}`
              
              // Create tab with loading content
              addTab(title, `Loading ${mediaType}...`)
              
              // Fetch the media data
              if (mediaType === 'chart') {
                fetch(`http://localhost:8000/api/media/${uuid}`)
                  .then(response => {
                    if (!response.ok) {
                      throw new Error(`HTTP ${response.status}`)
                    }
                    return response.blob()
                  })
                  .then(blob => {
                    const url = URL.createObjectURL(blob)
                    
                    // Update the tab content with the media
                    setTabs(prev => prev.map(tab => {
                      if (tab.title === title) {
                        return {
                          ...tab,
                          content: `<img src="${url}" alt="${title}" style="max-width: 100%; height: auto;" />`
                        }
                      }
                      return tab
                    }))
                  })
                  .catch(error => {
                    console.error('Failed to fetch media:', error)
                    // Update tab with error message
                    setTabs(prev => prev.map(tab => {
                      if (tab.title === title) {
                        return {
                          ...tab,
                          content: `<div style="color: red;">Failed to load media: ${error.message}</div>`
                        }
                      }
                      return tab
                    }))
                  })
              } else if (mediaType === 'dataframemedia') {
                fetch(`http://localhost:8000/api/media/${uuid}`)
                  .then(response => {
                    if (!response.ok) throw new Error(`HTTP ${response.status}`)
                    return response.json()
                  })
                  .then(json => {
                    setTabs(prev => prev.map(tab => {
                      if (tab.title === title) {
                        return {
                          ...tab,
                          content: <DataFrameTable schema={json.schema} data={json.data} />
                        }
                      }
                      return tab
                    }))
                  })
                  .catch(error => {
                    setTabs(prev => prev.map(tab => {
                      if (tab.title === title) {
                        return {
                          ...tab,
                          content: <div style={{ color: 'red' }}>Failed to load DataFrame: {error.message}</div>
                        }
                      }
                      return tab
                    }))
                  })
              } else {
                // Fallback for other media types
                setTabs(prev => prev.map(tab => {
                  if (tab.title === title) {
                    return {
                      ...tab,
                      content: `<div>Unsupported media type: ${mediaType}</div>`
                    }
                  }
                  return tab
                }))
              }
            }
          })
        }
      } catch (e) {
        addConsoleOutput(event.data)
      }
    }
    
    wsRef.current.onclose = () => {
      setIsConnected(false)
      isConnectingRef.current = false
      addConsoleOutput('WebSocket disconnected', 'error')
      
      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000)
    }
    
    wsRef.current.onerror = (error) => {
      isConnectingRef.current = false
      addConsoleOutput('WebSocket error: ' + error, 'error')
    }
  }
  
  const handleCommand = (command) => {
    if (!isConnected) {
      addConsoleOutput('Not connected to server')
      return
    }
    
    // Handle client-side commands
    if (command === 'Clear()') {
      setConsoleOutput([])
      setCommandInput('')
      return // Don't send to server
    }
    
    addConsoleOutput('> ' + command)
    
    // Add to history
    addToHistory(command)
    
    // Send command to WebSocket
    wsRef.current.send(JSON.stringify({
      type: 'command',
      command: command,
      session_id: sessionId
    }))
    
    setCommandInput('')
  }
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      const command = commandInput.trim()
      if (command) {
        handleCommand(command)
      }
    }
  }
  
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      navigateHistory('up')
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      navigateHistory('down')
    }
  }
  
  const addTab = (title, content) => {
    const newTab = {
      id: Date.now() + Math.random(), // Ensure unique ID
      title,
      content,
      type: 'table' // or 'plot'
    }
    setTabs(prev => [...prev, newTab])
    setActiveTab(newTab.id)
  }
  
  const maximizeTab = (tabId) => {
    setMaximizedTab(maximizedTab === tabId ? null : tabId)
  }
  
  const closeTab = (tabId) => {
    setTabs(prev => prev.filter(tab => tab.id !== tabId))
    if (activeTab === tabId) {
      // Set active tab to the next available tab, or null if none left
      setTabs(prev => {
        const remainingTabs = prev.filter(tab => tab.id !== tabId)
        if (remainingTabs.length > 0) {
          setActiveTab(remainingTabs[0].id)
        } else {
          setActiveTab(null)
        }
        return remainingTabs
      })
    }
    // If the maximized tab is closed, exit maximized mode
    if (maximizedTab === tabId) {
      setMaximizedTab(null)
    }
  }
  
  const moveTab = (fromIndex, toIndex) => {
    setTabs(prev => {
      const newTabs = [...prev]
      const [movedTab] = newTabs.splice(fromIndex, 1)
      newTabs.splice(toIndex, 0, movedTab)
      return newTabs
    })
  }
  
  // Resize handlers
  const handleMouseDown = (e) => {
    isResizingRef.current = true
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    e.preventDefault()
  }
  
  const handleTouchStart = (e) => {
    isResizingRef.current = true
    document.addEventListener('touchmove', handleTouchMove, { passive: false })
    document.addEventListener('touchend', handleTouchEnd)
    e.preventDefault()
  }
  
  const handleMouseMove = (e) => {
    if (!isResizingRef.current) return
    
    const newHeight = e.clientY
    const minMediaHeight = 50
    const minConsoleHeight = 50
    const maxHeight = window.innerHeight - minConsoleHeight - 60 // 60px for command input
    
    if (newHeight >= minMediaHeight && newHeight <= maxHeight) {
      setMediaHeight(newHeight)
    }
  }
  
  const handleTouchMove = (e) => {
    if (!isResizingRef.current) return
    
    const touch = e.touches[0]
    const newHeight = touch.clientY
    const minMediaHeight = 50
    const minConsoleHeight = 50
    const maxHeight = window.innerHeight - minConsoleHeight - 60 // 60px for command input
    
    if (newHeight >= minMediaHeight && newHeight <= maxHeight) {
      setMediaHeight(newHeight)
    }
    e.preventDefault()
  }
  
  const handleMouseUp = () => {
    isResizingRef.current = false
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }
  
  const handleTouchEnd = () => {
    isResizingRef.current = false
    document.removeEventListener('touchmove', handleTouchMove)
    document.removeEventListener('touchend', handleTouchEnd)
  }
  
  // Connect WebSocket on mount (only once)
  useEffect(() => {
    if (!hasInitializedRef.current) {
      hasInitializedRef.current = true
      connectWebSocket()
      addConsoleOutput(`Session ${sessionId}`)
      // Removed dummy tabs
    }
  }, [])
  
  // Focus command input on mount
  useEffect(() => {
    commandInputRef.current?.focus()
  }, [])
  
  return (
    <div className="app">
      {/* Media Output Area */}
      {!maximizedTab && (
        <div className="media-area" style={{ height: `${mediaHeight}px` }}>
          <div className="tab-bar">
            {tabs.map((tab, index) => (
              <div 
                key={tab.id} 
                className={`tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
                draggable
                onDragStart={(e) => {
                  e.dataTransfer.setData('text/plain', index.toString())
                }}
                onDragOver={(e) => {
                  e.preventDefault()
                }}
                onDrop={(e) => {
                  e.preventDefault()
                  const fromIndex = parseInt(e.dataTransfer.getData('text/plain'))
                  const toIndex = index
                  if (fromIndex !== toIndex) {
                    moveTab(fromIndex, toIndex)
                  }
                }}
              >
                <span className="tab-title">{tab.title}</span>
                <div className="tab-controls">
                  <button 
                    className="maximize-btn"
                    onClick={(e) => {
                      e.stopPropagation()
                      maximizeTab(tab.id)
                    }}
                    title="Maximize"
                  >
                    ⚡
                  </button>
                  <button 
                    className="close-btn"
                    onClick={(e) => {
                      e.stopPropagation()
                      closeTab(tab.id)
                    }}
                    title="Close"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="tab-content">
            {activeTab && tabs.find(t => t.id === activeTab)?.content}
          </div>
          
          {/* Resize Handle */}
          <div 
            className="resize-handle"
            onMouseDown={handleMouseDown}
            onTouchStart={handleTouchStart}
            ref={resizeRef}
          />
        </div>
      )}
      
      {/* Maximized Tab */}
      {maximizedTab && (
        <div className="maximized-tab">
          <div className="tab-header">
            <span>{tabs.find(t => t.id === maximizedTab)?.title}</span>
            <button onClick={() => setMaximizedTab(null)}>×</button>
          </div>
          <div className="tab-content">
            {tabs.find(t => t.id === maximizedTab)?.content}
          </div>
        </div>
      )}
      
      {/* Console Output Area */}
      <div className="console-area">
        <div 
          className="console-output" 
          ref={consoleOutputRef}
          style={{ overflowY: 'auto' }}
        >
          {consoleOutput.slice(-5).map(line => (
            <div key={line.id} className={`console-line ${line.type}`}
              dangerouslySetInnerHTML={{ __html: line.message }}
            />
          ))}
        </div>
      </div>
      
      {/* Command Input Area */}
      <div className="command-area">
        <div className="command-input-wrapper">
          <span className="prompt">{'>'}</span>
          <input
            ref={commandInputRef}
            type="text"
            value={commandInput}
            onChange={(e) => setCommandInput(e.target.value)}
            onKeyPress={handleKeyPress}
            onKeyDown={handleKeyDown}
            placeholder=""
            className="command-input"
            disabled={!isConnected}
          />
        </div>
      </div>
    </div>
  )
}

export default App
