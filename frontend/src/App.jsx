import { useState, useEffect } from 'react'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { TrendingUp, Upload, RefreshCw } from 'lucide-react'
import './index.css'

const API_URL = 'http://127.0.0.1:5000'

function App() {
  const [activeTab, setActiveTab] = useState('predict')
  const [trends, setTrends] = useState([])
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  
  // Form state for prediction
  const [formData, setFormData] = useState({
    product_name: '',
    cost_price: '',
    competitor_price: '',
    demand_level: 'Medium',
    stock: ''
  })
  
  const [prediction, setPrediction] = useState(null)

  // Load market trends on mount
  useEffect(() => {
    fetchTrends()
    fetchHistory()
  }, [])

  const fetchTrends = async () => {
    try {
      const response = await axios.get(`${API_URL}/market-trend`)
      setTrends(response.data.trends)
    } catch (error) {
      console.error('Error fetching trends:', error)
    }
  }

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API_URL}/history`)
      setHistory(response.data.history)
    } catch (error) {
      console.error('Error fetching history:', error)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handlePredict = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await axios.post(`${API_URL}/predict-price`, {
        ...formData,
        cost_price: parseFloat(formData.cost_price),
        competitor_price: parseFloat(formData.competitor_price),
        stock: parseInt(formData.stock)
      })
      setPrediction(response.data)
      fetchHistory()
    } catch (error) {
      alert('Error: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    const formDataFile = new FormData()
    formDataFile.append('file', file)
    
    setLoading(true)
    try {
      const response = await axios.post(`${API_URL}/upload-excel`, formDataFile, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      alert('File uploaded successfully! Processed ' + response.data.results.length + ' products')
      fetchHistory()
    } catch (error) {
      alert('Error: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <TrendingUp size={32} />
            <h1>AI Profit Optimization Engine</h1>
          </div>
          <p className="subtitle">Dynamic Pricing with Real-Time Market Data</p>
        </div>
      </header>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'predict' ? 'active' : ''}`}
          onClick={() => setActiveTab('predict')}
        >
          Price Prediction
        </button>
        <button 
          className={`tab ${activeTab === 'trends' ? 'active' : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          Market Trends
        </button>
        <button 
          className={`tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          History
        </button>
      </div>

      <main className="container">
        {/* Price Prediction Tab */}
        {activeTab === 'predict' && (
          <div className="tab-content">
            <div className="prediction-section">
              <div className="form-container">
                <h2>Get Price Prediction</h2>
                <form onSubmit={handlePredict}>
                  <div className="form-group">
                    <label>Product Name</label>
                    <input
                      type="text"
                      name="product_name"
                      value={formData.product_name}
                      onChange={handleInputChange}
                      placeholder="e.g., Premium Headphones"
                      required
                    />
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label>Cost Price ($)</label>
                      <input
                        type="number"
                        name="cost_price"
                        value={formData.cost_price}
                        onChange={handleInputChange}
                        placeholder="0.00"
                        step="0.01"
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>Competitor Price ($)</label>
                      <input
                        type="number"
                        name="competitor_price"
                        value={formData.competitor_price}
                        onChange={handleInputChange}
                        placeholder="0.00"
                        step="0.01"
                        required
                      />
                    </div>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label>Demand Level</label>
                      <select
                        name="demand_level"
                        value={formData.demand_level}
                        onChange={handleInputChange}
                      >
                        <option>Low</option>
                        <option>Medium</option>
                        <option>High</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Stock Units</label>
                      <input
                        type="number"
                        name="stock"
                        value={formData.stock}
                        onChange={handleInputChange}
                        placeholder="0"
                        required
                      />
                    </div>
                  </div>

                  <button type="submit" className="btn-primary" disabled={loading}>
                    {loading ? 'Analyzing...' : 'Get Optimized Price'}
                  </button>
                </form>

                <div className="upload-section">
                  <label className="upload-label">
                    <Upload size={20} />
                    Upload Excel/CSV File
                    <input
                      type="file"
                      accept=".xlsx,.csv"
                      onChange={handleFileUpload}
                      disabled={loading}
                      style={{ display: 'none' }}
                    />
                  </label>
                </div>
              </div>

              {prediction && (
                <div className="prediction-result">
                  <h3>Optimization Results for {prediction.product_name || 'Product'}</h3>
                  <div className="result-grid">
                    <div className="result-card">
                      <span className="label">Cost Price</span>
                      <span className="value">${(prediction.cost_price || 0).toFixed(2)}</span>
                    </div>
                    <div className="result-card">
                      <span className="label">Competitor Price</span>
                      <span className="value">${(prediction.competitor_price || 0).toFixed(2)}</span>
                    </div>
                    <div className="result-card highlight">
                      <span className="label">Optimized Price</span>
                      <span className="value">${(prediction.optimized_price || 0).toFixed(2)}</span>
                    </div>
                    <div className="result-card">
                      <span className="label">Profit Margin</span>
                      <span className="value">{(prediction.profit_margin || 0).toFixed(1)}%</span>
                    </div>
                  </div>
                  {prediction.ai_recommendation && (
                    <div className="ai-recommendation">
                      <h4>AI Recommendation</h4>
                      {typeof prediction.ai_recommendation === 'object' ? (
                        <div>
                          {prediction.ai_recommendation.pricing_suggestion && (
                            <p><strong>Pricing:</strong> {prediction.ai_recommendation.pricing_suggestion}</p>
                          )}
                          {prediction.ai_recommendation.market_insight && (
                            <p><strong>Market Insight:</strong> {prediction.ai_recommendation.market_insight}</p>
                          )}
                          {prediction.ai_recommendation.profit_advice && (
                            <p><strong>Profit Advice:</strong> {prediction.ai_recommendation.profit_advice}</p>
                          )}
                          {prediction.ai_recommendation.demand_explanation && (
                            <p><strong>Demand:</strong> {prediction.ai_recommendation.demand_explanation}</p>
                          )}
                        </div>
                      ) : (
                        <p>{prediction.ai_recommendation}</p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Market Trends Tab */}
        {activeTab === 'trends' && (
          <div className="tab-content">
            <div className="trends-section">
              <h2>Market Trends</h2>
              <button 
                className="btn-secondary"
                onClick={fetchTrends}
                disabled={loading}
              >
                <RefreshCw size={16} /> Refresh
              </button>
              
              {trends.length > 0 && (
                <>
                  <div className="chart-container">
                    <h3>Demand vs Competition</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={trends}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line 
                          type="monotone" 
                          dataKey="demand" 
                          stroke="#8884d8" 
                          name="Demand"
                        />
                        <Line 
                          type="monotone" 
                          dataKey="competitorAvg" 
                          stroke="#82ca9d" 
                          name="Competitor Avg Price"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  <div className="chart-container">
                    <h3>Monthly Comparison</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={trends}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="demand" fill="#8884d8" name="Demand" />
                        <Bar dataKey="competitorAvg" fill="#82ca9d" name="Competitor Avg" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="tab-content">
            <div className="history-section">
              <h2>Prediction History</h2>
              {history.length === 0 ? (
                <p className="empty-message">No predictions yet. Make a prediction to get started!</p>
              ) : (
                <div className="history-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Cost</th>
                        <th>Competitor</th>
                        <th>Optimized Price</th>
                        <th>Margin</th>
                        <th>Demand</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.product_name || 'N/A'}</td>
                          <td>${(item.cost_price || 0).toFixed(2)}</td>
                          <td>${(item.competitor_price || 0).toFixed(2)}</td>
                          <td className="highlight">${(item.optimized_price || 0).toFixed(2)}</td>
                          <td>{(item.profit_margin || 0).toFixed(1)}%</td>
                          <td>{item.demand_level || 'N/A'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>AI Based Profit Optimization Engine • Dynamic Pricing with Real-Time Market Data</p>
      </footer>
    </div>
  )
}

export default App
