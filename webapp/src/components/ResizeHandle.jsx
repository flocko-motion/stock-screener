import React, { useCallback } from 'react'

function ResizeHandle({ mediaHeight, setMediaHeight, isResizingRef }) {
  const handleMouseMove = useCallback((e) => {
    if (!isResizingRef.current) return
    const newHeight = e.clientY
    const minMediaHeight = 50
    const minConsoleHeight = 50
    const maxHeight = window.innerHeight - minConsoleHeight - 60 // 60px for command input
    if (newHeight >= minMediaHeight && newHeight <= maxHeight) {
      setMediaHeight(newHeight)
    }
  }, [setMediaHeight, isResizingRef])

  const handleMouseUp = useCallback(() => {
    isResizingRef.current = false
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }, [handleMouseMove, isResizingRef])

  const handleTouchMove = useCallback((e) => {
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
  }, [setMediaHeight, isResizingRef])

  const handleTouchEnd = useCallback(() => {
    isResizingRef.current = false
    document.removeEventListener('touchmove', handleTouchMove)
    document.removeEventListener('touchend', handleTouchEnd)
  }, [handleTouchMove, isResizingRef])

  const handleMouseDown = useCallback((e) => {
    isResizingRef.current = true
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    e.preventDefault()
  }, [handleMouseMove, handleMouseUp, isResizingRef])

  const handleTouchStart = useCallback((e) => {
    isResizingRef.current = true
    document.addEventListener('touchmove', handleTouchMove, { passive: false })
    document.addEventListener('touchend', handleTouchEnd)
    e.preventDefault()
  }, [handleTouchMove, handleTouchEnd, isResizingRef])

  return (
    <div 
      className="resize-handle"
      onMouseDown={handleMouseDown}
      onTouchStart={handleTouchStart}
    />
  )
}

export default ResizeHandle 