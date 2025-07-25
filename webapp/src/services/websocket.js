class WebSocketService {
  constructor() {
    this.ws = null
    this.isConnecting = false
    this.reconnectTimeout = null
    this.messageHandlers = new Map()
    this.connectionHandlers = new Map()
    this.mediaHandlers = new Map()
    this.sessionId = Math.floor(Math.random() * 1000000)
  }

  // Register message handlers
  onMessage(type, handler) {
    this.messageHandlers.set(type, handler)
  }

  // Register connection state handlers
  onConnectionChange(handler) {
    this.connectionHandlers.set('change', handler)
  }

  // Register media handlers
  onMedia(mediaType, handler) {
    this.mediaHandlers.set(mediaType, handler)
  }

  // Connect to WebSocket
  connect() {
    console.log('WebSocketService.connect() called, current state:', {
      isConnecting: this.isConnecting,
      wsState: this.ws?.readyState,
      wsExists: !!this.ws
    })
    
    if (this.isConnecting || this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING) {
      console.log('WebSocketService.connect() - already connecting or connected, skipping')
      return
    }
    
    console.log('WebSocketService.connect() - proceeding with connection')
    
    this.isConnecting = true
    
    try {
      console.log('WebSocket - creating WebSocket instance')
      this.ws = new WebSocket('ws://localhost:8001')
      
      this.ws.onopen = () => {
        console.log('WebSocket - connection opened')
        this.isConnecting = false
        this.notifyConnectionChange(true)
      }
      
      this.ws.onclose = () => {
        console.log('WebSocket - connection closed')
        this.isConnecting = false
        this.notifyConnectionChange(false)
      }
      
      this.ws.onerror = (error) => {
        console.log('WebSocket - connection error:', error)
        // Only log error if WebSocket is not already closed (cleanup scenario)
        if (this.ws?.readyState !== WebSocket.CLOSED) {
          console.log('WebSocket error:', error)
        }
      }
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleMessage(data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }
    } catch (error) {
      console.error('Error creating WebSocket:', error)
      this.isConnecting = false
      this.notifyConnectionChange(false)
    }
  }

  // Handle incoming messages
  handleMessage(data) {
    if (data.type === 'media') {
      this.handleMediaMessage(data)
    } else {
      const handler = this.messageHandlers.get(data.type)
      if (handler) {
        handler(data)
      } else {
        // Default handler for unknown message types
        console.log('Unhandled message type:', data.type, data)
      }
    }
  }

  // Handle media messages
  handleMediaMessage(data) {
    console.log('Received media handles:', data.handles)
    data.handles.forEach(handle => {
      // Parse handle format: [type:uuid]
      const match = handle.match(/\[(\w+):([a-f0-9-]+)\]/)
      if (match) {
        const [, mediaType, uuid] = match
        const title = mediaType === 'dataframemedia' ? `DF ${uuid.slice(0, 4)}` : `${mediaType.charAt(0).toUpperCase() + mediaType.slice(1)} ${uuid.slice(0, 8)}`
        
        // Notify about new media with loading state
        this.notifyMedia(mediaType, { title, uuid, status: 'loading' })
        
        // Fetch the media data
        this.fetchMedia(mediaType, uuid, title)
      }
    })
  }

  // Fetch media data
  fetchMedia(mediaType, uuid, title) {
    if (mediaType === 'chart') {
      this.fetchChart(uuid, title)
    } else if (mediaType === 'dataframemedia') {
      this.fetchDataFrame(uuid, title)
    } else {
      // Fallback for other media types
      this.notifyMedia(mediaType, {
        title,
        uuid,
        status: 'error',
        content: `<div>Unsupported media type: ${mediaType}</div>`
      })
    }
  }

  // Fetch chart media
  fetchChart(uuid, title) {
    fetch(`http://localhost:8000/api/media/${uuid}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        return response.blob()
      })
      .then(blob => {
        const url = URL.createObjectURL(blob)
        this.notifyMedia('chart', {
          title,
          uuid,
          status: 'success',
          content: `<img src="${url}" alt="${title}" style="max-width: 100%; height: auto;" />`
        })
      })
      .catch(error => {
        console.error('Failed to fetch chart:', error)
        this.notifyMedia('chart', {
          title,
          uuid,
          status: 'error',
          content: `<div style="color: red;">Failed to load media: ${error.message}</div>`
        })
      })
  }

  // Fetch DataFrame media
  fetchDataFrame(uuid, title) {
    fetch(`http://localhost:8000/api/media/${uuid}`)
      .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        return response.json()
      })
      .then(json => {
        this.notifyMedia('dataframemedia', {
          title,
          uuid,
          status: 'success',
          content: { schema: json.schema, data: json.data }
        })
      })
      .catch(error => {
        this.notifyMedia('dataframemedia', {
          title,
          uuid,
          status: 'error',
          content: `<div style="color: red;">Failed to load DataFrame: ${error.message}</div>`
        })
      })
  }

  // Notify media handlers
  notifyMedia(mediaType, data) {
    const handler = this.mediaHandlers.get(mediaType)
    if (handler) {
      handler(data)
    } else {
      // Default handler for all media types
      const defaultHandler = this.mediaHandlers.get('*')
      if (defaultHandler) {
        defaultHandler(mediaType, data)
      }
    }
  }

  // Notify connection state change
  notifyConnectionChange(isConnected) {
    const handler = this.connectionHandlers.get('change')
    if (handler) {
      handler(isConnected)
    }
  }

  // Send command to server
  sendCommand(command) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'command',
        command: command,
        session_id: this.sessionId
      }))
      return true
    }
    return false
  }

  // Get connection state
  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN
  }

  // Get session ID
  getSessionId() {
    return this.sessionId
  }
}

export default WebSocketService