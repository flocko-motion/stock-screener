import React from 'react'

function TabBar({ 
  tabs, 
  activeTab, 
  setActiveTab, 
  maximizeTab, 
  closeTab, 
  moveTab 
}) {
  return (
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
  )
}

export default TabBar 