import React, { useState, useRef, useEffect } from 'react'
import './App.css'
import DataFrameTable from './components/DataFrameTable'
import Console from './components/Console'
import TabBar from './components/TabBar'
import ResizeHandle from './components/ResizeHandle'
import WebSocketService from './services/websocket'

function App() {
  const [isConnected, setIsConnected] = useState(false)
  const [tabs, setTabs] = useState([])
  const [activeTab, setActiveTab] = useState(null)
  const [maximizedTab, setMaximizedTab] = useState(null)
  const [mediaHeight, setMediaHeight] = useState(() => window.innerHeight - 200)
  
  const wsServiceRef = useRef(null)
  const consoleRef = useRef(null)
  const hasInitializedRef = useRef(false)
  const isResizingRef = useRef(false)
  
  const setTabContent = (id, title, content) => {
    setTabs(prev => {
      const existingTab = prev.find(tab => tab.id === id)
      if (existingTab) {
        // Update existing tab
        return prev.map(tab => 
          tab.id === id ? { ...tab, content } : tab
        )
      } else {
        // Create new tab
        const newTab = { id, title, content, type: 'table' }
        setActiveTab(id)
        return [...prev, newTab]
      }
    })
  }
  
  const initializeWebSocket = () => {
    if (wsServiceRef.current) {
      console.log('WebSocket already initialized, skipping')
      return
    }
    
    console.log('Initializing WebSocket service')
    wsServiceRef.current = new WebSocketService()
    
    wsServiceRef.current.onConnectionChange((connected) => {
      setIsConnected(connected)
      if (connected) {
        consoleRef.current?.addConsoleOutput('Connected')
      } else {
        consoleRef.current?.addConsoleOutput('WebSocket disconnected')
      }
    })
    
    wsServiceRef.current.onMessage('output', (data) => {
      consoleRef.current?.addConsoleOutput(data.content)
    })
    
    wsServiceRef.current.onMessage('error', (data) => {
      consoleRef.current?.addConsoleOutput(data.content, 'error')
    })
    
    wsServiceRef.current.onMedia('chart', (data) => {
      const { uuid, title, content } = data
      setTabContent(uuid, `Chart ${title}`, <img src={content} alt={title} style={{ maxWidth: '100%', height: 'auto' }} />)
    })
    
    wsServiceRef.current.onMedia('dataframemedia', (data) => {
      console.log('Received dataframemedia data:', data)
      const { content, status } = data
      const tabTitle = `DF ${data.uuid.slice(0, 4)}`
      
      if (status === 'loading') {
        setTabContent(data.uuid, tabTitle, <div>Loading DataFrame...</div>)
      } else if (content && content.schema && content.data) {
        setTabContent(data.uuid, tabTitle, <DataFrameTable schema={content.schema} data={content.data} tableId={data.uuid} />)
      } else {
        console.error('Invalid DataFrame data structure:', data)
      }
    })
    
    console.log('App - calling wsServiceRef.current.connect()')
    wsServiceRef.current.connect()
  }
  
  const handleCommand = (command) => {
    // Send command via WebSocket service
    const sent = wsServiceRef.current.sendCommand(command)
    if (!sent) {
      consoleRef.current?.addConsoleOutput('Failed to send command - not connected', 'error')
    }
  }
  
  const maximizeTab = (tabId) => {
    setMaximizedTab(maximizedTab === tabId ? null : tabId)
  }
  
  const closeTab = (tabId) => {
    setTabs(prev => prev.filter(tab => tab.id !== tabId))
    if (activeTab === tabId) {
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
  
  // Initialize WebSocket on mount
  useEffect(() => {
    console.log('App useEffect - initialization phase')
    if (!hasInitializedRef.current) {
      console.log('App useEffect - first time initialization')
      hasInitializedRef.current = true
      initializeWebSocket()
      consoleRef.current?.addConsoleOutput(`Session ${wsServiceRef.current?.getSessionId()}`)
    }
  }, [])
  
  return (
    <div className="app">
      {/* Media Output Area */}
      {!maximizedTab && (
        <div className="media-area" style={{ height: `${mediaHeight}px` }}>
          <TabBar 
            tabs={tabs}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            maximizeTab={maximizeTab}
            closeTab={closeTab}
            moveTab={moveTab}
          />
          <div className="tab-content">
            {activeTab && tabs.find(t => t.id === activeTab)?.content}
          </div>
          
          {/* Resize Handle */}
          <ResizeHandle 
            mediaHeight={mediaHeight}
            setMediaHeight={setMediaHeight}
            isResizingRef={isResizingRef}
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
      
      {/* Console Component */}
      <Console 
        ref={consoleRef}
        handleCommand={handleCommand}
        isConnected={isConnected}
      />
    </div>
  )
}

export default App
