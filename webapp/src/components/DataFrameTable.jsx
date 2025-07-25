import React, { useState } from 'react'
import { useReactTable, getCoreRowModel, getSortedRowModel, getFilteredRowModel, getPaginationRowModel, flexRender, createColumnHelper } from '@tanstack/react-table'

function DataFrameTable({ schema, data, tableId }) {
  // Create column helper inside component to ensure each instance gets its own
  const columnHelper = React.useMemo(() => createColumnHelper(), [])
  
  const [columnOrder, setColumnOrder] = useState([])
  const [columnVisibility, setColumnVisibility] = useState({})
  const [columnFilters, setColumnFilters] = useState([])
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: 10,
  })
  const [movingColumnId, setMovingColumnId] = useState(null)
  const [targetColumnId, setTargetColumnId] = useState(null)
  
  // Debug: log when column visibility changes
  React.useEffect(() => {
    console.log(`Table ${tableId} column visibility:`, columnVisibility)
  }, [columnVisibility, tableId])
  
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
    tableId: tableId, // Add unique table ID
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
            
            {/* Unified Show/Columns Dropdown */}
            <div className="column-dropdown">
              <select
                value=""
                onChange={e => {
                  const value = e.target.value
                  
                  // Handle page size options
                  if (value.startsWith('page-size-')) {
                    const pageSize = value.replace('page-size-', '')
                    const actualPageSize = pageSize === 'ALL' ? (() => {
                      const totalRows = table.getFilteredRowModel().rows.length
                      return totalRows
                    })() : Number(pageSize)
                    table.setPageSize(actualPageSize)
                  }
                  // Handle column visibility options
                  else if (value === 'show-all') {
                    table.toggleAllColumnsVisible()
                  } else if (value === 'hide-all') {
                    table.toggleAllColumnsVisible()
                  } else if (value && !value.startsWith('page-size-')) {
                    const column = table.getColumn(value)
                    if (column) {
                      column.toggleVisibility()
                    }
                  }
                  e.target.value = "" // Reset selection
                }}
              >
                <option value="">Settings</option>
                {(() => {
                  const totalRows = table.getFilteredRowModel().rows.length
                  const pageSizeOptions = [10, 100, 1000, totalRows]
                  
                  return pageSizeOptions.map((pageSize, index) => (
                    <option key={`page-size-${pageSize}-${index}`} value={`page-size-${pageSize === totalRows ? 'ALL' : pageSize}`}>
                      {index === pageSizeOptions.length - 1 ? 'ALL' : pageSize}
                    </option>
                  ))
                })()}
                <option value="" disabled>──────────</option>
                <option value={table.getIsAllColumnsVisible() ? 'hide-all' : 'show-all'}>
                  {table.getIsAllColumnsVisible() ? '(All)' : '(All)'}
                </option>
                {table.getAllLeafColumns()
                  .filter(column => column.getCanHide())
                  .map(column => (
                    <option key={column.id} value={column.id}>
                      {column.getIsVisible() ? '✓ ' : '  '}{column.id}
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

export default DataFrameTable 