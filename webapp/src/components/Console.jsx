import React, { useRef, useEffect, useState, forwardRef, useImperativeHandle } from 'react'
import { convertAnsiToHtml } from '../utils/ansi'

const Console = forwardRef(({ handleCommand, isConnected }, ref) => {
  const [commandInput, setCommandInput] = useState('')
  const [consoleOutput, setConsoleOutput] = useState([])
  const consoleOutputRef = useRef(null)
  const commandInputRef = useRef(null)
  
  // Command history
  const commandHistoryRef = useRef([])
  const historyIndexRef = useRef(-1)
  const currentInputRef = useRef('')
  
  const addConsoleOutput = (message, type = 'info') => {
    setConsoleOutput(prev => [...prev, { 
      id: Date.now(), 
      message: message, 
      type,
      timestamp: new Date() 
    }])
  }
  
  // Expose addConsoleOutput method to parent
  useImperativeHandle(ref, () => ({
    addConsoleOutput
  }))
  
  // Auto-scroll console to bottom when new output is added
  useEffect(() => {
    if (consoleOutputRef.current) {
      consoleOutputRef.current.scrollTop = consoleOutputRef.current.scrollHeight
    }
  }, [consoleOutput])
  
  // Focus command input on mount
  useEffect(() => {
    commandInputRef.current?.focus()
  }, [])
  
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
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      const command = commandInput.trim()
      if (command) {
        // Handle client-side commands
        if (command === 'Clear()') {
          setConsoleOutput([])
          setCommandInput('')
          return
        }
        
        addToHistory(command)
        addConsoleOutput('> ' + command)
        
        // Check connection before sending command
        if (!isConnected) {
          addConsoleOutput('Not connected to server')
          setCommandInput('')
          return
        }
        
        handleCommand(command)
        setCommandInput('')
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
  
  return (
    <>
      {/* Console Output Area */}
      <div className="console-area">
        <div 
          className="console-output" 
          ref={consoleOutputRef}
          style={{ overflowY: 'auto' }}
        >
          {consoleOutput.slice(-5).map(line => (
            <div key={line.id} className={`console-line ${line.type}`}
              dangerouslySetInnerHTML={{ __html: convertAnsiToHtml(line.message) }}
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
    </>
  )
})

Console.displayName = 'Console'

export default Console 