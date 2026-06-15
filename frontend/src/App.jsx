import { useState, useEffect } from 'react'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { TrendingUp, Upload, RefreshCw } from 'lucide-react'
import './index.css'

const API_URL = '/api'

const formatMetric = (value, digits = 3) => {
  const numericValue = Number(value)
  return Number.isFinite(numericValue) ? numericValue.toFixed(digits) : 'N/A'
}

const getTrainedModels = (report) => {
  if (!report?.models) return []

  return Object.entries(report.models)
    .filter(([, metrics]) => metrics?.status === 'trained')
    .sort(([, a], [, b]) => (Number(b?.accuracy) || 0) - (Number(a?.accuracy) || 0))
}

function App() {
  const [activeTab, setActiveTab] = useState('predict')
  const [trends, setTrends] = useState([])
  const [history, setHistory] = useState([])
  const [products, setProducts] = useState([])
  const [selectedProduct, setSelectedProduct] = useState('')
  const [productInsights, setProductInsights] = useState(null)
  const [modelPerformance, setModelPerformance] = useState(null)
  const [loading, setLoading] = useState(false)
  const [dashboardLoading, setDashboardLoading] = useState(false)
  const [insightsLoading, setInsightsLoading] = useState(false)
  const [trainingModels, setTrainingModels] = useState(false)
  const [dashboardError, setDashboardError] = useState('')

  const bestModelSummary = () => {
    const trainedModels = getTrainedModels(modelPerformance)

    if (trainedModels.length === 0) return null
    const [modelKey, metrics] = trainedModels[0]
    return { modelKey, metrics }
  }
  
  // Form state for prediction
  const [formData, setFormData] = useState({
    product_name: '',
    cost_price: '',
    competitor_price: '',
    current_price: '',
    historical_sales: '',
    stock: '',
    customer_interest: 50,
    seasonal_factor: 1.0,
    market_trend: 1.0
  })
  
  const [prediction, setPrediction] = useState(null)

  // Load market trends on mount
  useEffect(() => {
    fetchTrends()
    fetchHistory()
  }, [])

  const fetchProducts = async () => {
    const response = await axios.get(`${API_URL}/products`)
    return response.data.products || []
  }

  const fetchProductInsights = async (productName) => {
    if (!productName) {
      setProductInsights(null)
      return
    }

    setInsightsLoading(true)
    try {
      const response = await axios.get(`${API_URL}/product-insights`, {
        params: { product_name: productName }
      })
      setProductInsights(response.data.insights || null)
    } catch (error) {
      console.error('Error fetching product insights:', error)
      setProductInsights(null)
      setDashboardError(error.response?.data?.error || 'Unable to load product insights right now.')
    } finally {
      setInsightsLoading(false)
    }
  }

  const fetchModelPerformance = async () => {
    const response = await axios.get(`${API_URL}/model-performance`)
    return response.data.model_performance || null
  }

  const loadAnalyticsDashboard = async () => {
    setDashboardLoading(true)
    setDashboardError('')

    try {
      const [productList, performanceReport] = await Promise.all([
        fetchProducts(),
        fetchModelPerformance()
      ])

      setProducts(productList)
      setModelPerformance(performanceReport)

      if (selectedProduct) {
        await fetchProductInsights(selectedProduct)
      }
    } catch (error) {
      console.error('Error loading analytics dashboard:', error)
      setProducts([])
      setModelPerformance(null)
      setDashboardError(error.response?.data?.error || 'Unable to load analytics dashboard.')
    } finally {
      setDashboardLoading(false)
    }
  }

  const handleTrainModels = async () => {
    setTrainingModels(true)
    setDashboardError('')

    try {
      await axios.post(`${API_URL}/retrain-model`, {
        model_type: 'all',
        force: true,
        bootstrap_data: true
      })

      await loadAnalyticsDashboard()
      if (selectedProduct) {
        await fetchProductInsights(selectedProduct)
      }
    } catch (error) {
      console.error('Error training models:', error)
      setDashboardError(error.response?.data?.error || 'Model training failed.')
    } finally {
      setTrainingModels(false)
    }
  }

  const handleProductSelect = async (e) => {
    const selection = e.target.value
    setSelectedProduct(selection)
    await fetchProductInsights(selection)
  }

  useEffect(() => {
    if (activeTab === 'analytics') {
      loadAnalyticsDashboard()
    }
  }, [activeTab])

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
        current_price: parseFloat(formData.current_price),
        historical_sales: formData.historical_sales ? parseInt(formData.historical_sales, 10) : 0,
        stock: parseInt(formData.stock, 10),
        customer_interest: parseFloat(formData.customer_interest),
        seasonal_factor: parseFloat(formData.seasonal_factor),
        market_trend: parseFloat(formData.market_trend)
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
          className={`tab ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          Analytics
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
                      <label>Current Price ($)</label>
                      <input
                        type="number"
                        name="current_price"
                        value={formData.current_price}
                        onChange={handleInputChange}
                        placeholder="0.00"
                        step="0.01"
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>Historical Sales</label>
                      <input
                        type="number"
                        name="historical_sales"
                        value={formData.historical_sales}
                        onChange={handleInputChange}
                        placeholder="Units sold in past period"
                        step="1"
                        min="0"
                      />
                    </div>
                    <div className="form-group">
                      <label>Market Trend</label>
                      <input
                        type="number"
                        name="market_trend"
                        value={formData.market_trend}
                        onChange={handleInputChange}
                        placeholder="1.0"
                        min="0.5"
                        max="2.0"
                        step="0.05"
                        required
                      />
                    </div>
                  </div>

                              <div className="form-row">
                    <div className="form-group">
                      <label>Customer Interest Score</label>
                      <input
                        type="number"
                        name="customer_interest"
                        value={formData.customer_interest}
                        onChange={handleInputChange}
                        placeholder="50"
                        min="0"
                        max="100"
                        step="1"
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>Seasonal Factor</label>
                      <input
                        type="number"
                        name="seasonal_factor"
                        value={formData.seasonal_factor}
                        onChange={handleInputChange}
                        placeholder="1.0"
                        min="0.5"
                        max="2.0"
                        step="0.05"
                        required
                      />
                    </div>
                  </div>
                  <div className="form-row">
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
                      <span className="label">Final Applied Price</span>
                      <span className="value">${(prediction.final_price || 0).toFixed(2)}</span>
                    </div>
                    <div className="result-card">
                      <span className="label">AI Demand Forecast</span>
                      <span className="value">{prediction.predicted_demand || 0} units</span>
                    </div>
                    <div className="result-card">
                      <span className="label">Demand Confidence</span>
                      <span className="value">{(prediction.demand_confidence || 0).toFixed(1)}%</span>
                    </div>
                    <div className="result-card">
                      <span className="label">Profit Margin</span>
                      <span className="value">{(prediction.profit_margin_percent || 0).toFixed(1)}%</span>
                    </div>
                    <div className="result-card">
                      <span className="label">Profit Forecast</span>
                      <span className="value">${(prediction.expected_profit || 0).toFixed(2)}</span>
                    </div>
                    <div className="result-card">
                      <span className="label">Revenue Forecast</span>
                      <span className="value">${(prediction.expected_revenue || 0).toFixed(2)}</span>
                    </div>
                    <div className="result-card">
                      <span className="label">Baseline Profit</span>
                      <span className="value">${(prediction.explanation?.current_profit || 0).toFixed(2)}</span>
                    </div>
                    <div className="result-card">
                      <span className="label">Profit Increase</span>
                      <span className="value">${(prediction.explanation?.profit_increase || 0).toFixed(2)}</span>
                    </div>
                  </div>

                  {prediction.explanation && (
                    <div className="explanation-card">
                      <h4>Why this price was chosen</h4>
                      <p>{prediction.explanation.reason}</p>
                      <ul>
                        <li>Expected profit increase: ${prediction.explanation.profit_increase?.toFixed(2) || 0} ({prediction.explanation.profit_increase_pct?.toFixed(1) || 0}%)</li>
                        <li>Competitor comparison: {prediction.explanation.competitor_comparison}</li>
                        <li>Demand impact: {prediction.explanation.demand_impact >= 0 ? '+' : ''}{prediction.explanation.demand_impact} units vs current price</li>
                        <li>Baseline demand at current price: {prediction.explanation.baseline_demand || 0} units</li>
                      </ul>
                    </div>
                  )}

                  {prediction.candidate_scenarios && prediction.candidate_scenarios.length > 0 && (
                    <div className="scenario-table">
                      <h4>Evaluated Pricing Scenarios</h4>
                      <table>
                        <thead>
                          <tr>
                            <th>Price</th>
                            <th>Predicted Demand</th>
                            <th>Forecast Profit</th>
                            <th>Forecast Revenue</th>
                            <th>Change vs Current</th>
                            <th>Competitor Gap</th>
                          </tr>
                        </thead>
                        <tbody>
                          {prediction.candidate_scenarios.map((scenario, idx) => (
                            <tr key={idx} className={scenario.candidate_price === prediction.optimized_price ? 'selected-scenario' : ''}>
                              <td>${scenario.candidate_price.toFixed(2)}</td>
                              <td>{scenario.predicted_demand}</td>
                              <td>${scenario.predicted_profit.toFixed(2)}</td>
                              <td>${scenario.predicted_revenue.toFixed(2)}</td>
                              <td>{scenario.price_change_pct.toFixed(1)}%</td>
                              <td>{scenario.competitor_gap !== null ? `$${scenario.competitor_gap.toFixed(2)}` : 'N/A'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {prediction.ai_recommendations && prediction.ai_recommendations.length > 0 && (
                    <div className="ai-recommendation">
                      <h4>AI Recommendations</h4>
                      {prediction.ai_recommendations.map((rec, idx) => (
                        <div key={idx} className="recommendation-card">
                          <h5>{rec.title}</h5>
                          <p>{rec.recommendation}</p>
                          <span className="rec-meta">Priority: {rec.priority}</span>
                        </div>
                      ))}
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

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div className="tab-content">
            <div className="analytics-section">
              <div className="analytics-header">
                <div>
                  <h2>Analytics Dashboard</h2>
                  <p>Live product insights, model performance, and pricing stability metrics.</p>
                </div>
                <div className="analytics-actions">
                  <button 
                    className="btn-secondary"
                    onClick={handleTrainModels}
                    disabled={trainingModels || dashboardLoading}
                  >
                    {trainingModels ? 'Training Models...' : 'Train Models'}
                  </button>
                  <button 
                    className="btn-secondary"
                    onClick={loadAnalyticsDashboard}
                    disabled={dashboardLoading || trainingModels}
                  >
                    <RefreshCw size={16} /> Refresh Analytics
                  </button>
                </div>
              </div>

              <div className="analytics-controls">
                <label>
                  Select Product
                  <select value={selectedProduct} onChange={handleProductSelect}>
                    <option value="">Choose a product</option>
                    {products.map(product => (
                      <option key={product.product_id} value={product.product_name}>
                        {product.product_name}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              {dashboardLoading && <p>Loading analytics...</p>}

              {dashboardError && !dashboardLoading && (
                <div className="alert-card alert-danger">
                  <strong>Analytics issue:</strong>
                  <p>{dashboardError}</p>
                </div>
              )}

              {modelPerformance && !dashboardLoading && (() => {
                const summary = bestModelSummary()
                return summary ? (
                  <>
                    <div className="summary-grid">
                      <div className="summary-card">
                        <h3>Top Model Insight</h3>
                        <p className="summary-label">Best performing model</p>
                        <p className="summary-value">{summary.modelKey.replace('_', ' ').toUpperCase()}</p>
                        <div className="summary-details">
                          <span>Accuracy: {formatMetric(summary.metrics.accuracy)}</span>
                          <span>RMSE: {formatMetric(summary.metrics.rmse)}</span>
                          <span>Trend: {summary.metrics.performance_trend || 'unknown'}</span>
                        </div>
                      </div>
                      <div className="summary-card">
                        <h3>Latest Model Version</h3>
                        <p className="summary-label">Version</p>
                        <p className="summary-value">{summary.metrics.version || 'N/A'}</p>
                        <div className="summary-details">
                          <span>Samples: {summary.metrics.samples_used}</span>
                          <span>Last trained: {new Date(summary.metrics.latest_training || Date.now()).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                    {summary.metrics.drift_warning && (
                      <div className={`alert-card ${summary.metrics.performance_trend === 'degrading' ? 'alert-danger' : 'alert-warning'}`}>
                        <strong>Drift Warning:</strong>
                        <p>{summary.metrics.drift_warning}</p>
                      </div>
                    )}
                  </>
                ) : null
              })()}

              {modelPerformance && !dashboardLoading && getTrainedModels(modelPerformance).length === 0 && (
                <div className="summary-card analytics-empty-state">
                  <h3>No trained models available</h3>
                  <p>The analytics dashboard can train the forecasting models and seed sample data if the database is empty.</p>
                </div>
              )}

              {insightsLoading && !dashboardLoading && <p>Loading product insights...</p>}

              {productInsights && !insightsLoading && (
                <>
                  <div className="insights-grid">
                    <div className="insight-card">
                      <h3>Current Price</h3>
                      <p>₹{productInsights.product?.current_price?.toFixed(2) || 'N/A'}</p>
                    </div>
                    <div className="insight-card">
                      <h3>Stock Quantity</h3>
                      <p>{productInsights.product?.stock_quantity ?? 'N/A'}</p>
                    </div>
                    <div className="insight-card">
                      <h3>Interest Score</h3>
                      <p>{productInsights.behavior?.interest_score ?? 'N/A'}</p>
                    </div>
                    <div className="insight-card">
                      <h3>Price Sensitivity</h3>
                      <p>{productInsights.behavior?.price_sensitivity_score ?? 'N/A'}</p>
                    </div>
                    <div className="insight-card">
                      <h3>Volatility Score</h3>
                      <p>{productInsights.volatility_score != null ? `${productInsights.volatility_score}%` : 'N/A'}</p>
                    </div>
                    <div className="insight-card">
                      <h3>Forecast Demand</h3>
                      <p>{productInsights.demand_forecast?.predicted_demand ?? 'N/A'}</p>
                    </div>
                    <div className="insight-card">
                      <h3>Recommended Category</h3>
                      <p>{productInsights.pricing_decision?.pricing_category ?? 'N/A'}</p>
                    </div>
                  </div>

                  {productInsights.price_history?.length > 0 && (
                    <div className="stability-section">
                      <h3>Pricing Stability</h3>
                      <ResponsiveContainer width="100%" height={260}>
                        <LineChart data={[...productInsights.price_history].reverse()}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="price_change_date" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                          <YAxis />
                          <Tooltip formatter={(value) => `${value}%`} />
                          <Legend />
                          <Line type="monotone" dataKey="change_percent" stroke="#2563eb" name="Change %" />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </>
              )}

              {modelPerformance && !dashboardLoading && (
                <div className="performance-section">
                  <h3>Model Performance</h3>
                  {Object.entries(modelPerformance.models || {}).map(([key, metrics]) => (
                    <div key={key} className="performance-card">
                      <h4>{key.replace('_', ' ').toUpperCase()}</h4>
                      <p>Status: {metrics.status}</p>
                      {metrics.status === 'trained' && (
                        <ul>
                          <li>Accuracy: {formatMetric(metrics.accuracy)}</li>
                          <li>RMSE: {formatMetric(metrics.rmse)}</li>
                          <li>MAE: {formatMetric(metrics.mae)}</li>
                          <li>Samples: {metrics.samples_used ?? 'N/A'}</li>
                          <li>Trend: {metrics.performance_trend || 'unknown'}</li>
                        </ul>
                      )}
                      {metrics.status !== 'trained' && metrics.message && <p>{metrics.message}</p>}
                    </div>
                  ))}
                </div>
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
                          <td>{(item.profit_margin_percent || item.profit_margin || 0).toFixed(1)}%</td>
                          <td>{item.predicted_demand != null ? item.predicted_demand : item.demand_level || 'N/A'}</td>
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
