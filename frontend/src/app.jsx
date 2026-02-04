import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Area, AreaChart
} from 'recharts';
import { Camera, Package, TrendingUp, AlertTriangle, Plus, Search, Upload, Download, Edit, Trash2, ArrowUpCircle, ArrowDownCircle, Activity, DollarSign, Boxes } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL;

fetch(`${API_BASE}/products`)

// Utility function for API calls
const apiCall = async (endpoint, options = {}) => {
  const response = await fetch(`${API_URL}${endpoint}`, options);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'API Error');
  }
  return response.json();
};

// Dashboard Component
const Dashboard = ({ onNavigate }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const data = await apiCall('/api/dashboard');
      setStats(data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl p-6 border border-amber-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-amber-800">สินค้าทั้งหมด</p>
              <p className="text-3xl font-bold text-amber-900 mt-2">{stats?.total_products || 0}</p>
            </div>
            <div className="bg-amber-200 rounded-full p-3">
              <Package className="w-8 h-8 text-amber-700" />
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-red-50 to-rose-50 rounded-xl p-6 border border-red-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-red-800">ต้องสั่งซื้อ</p>
              <p className="text-3xl font-bold text-red-900 mt-2">{stats?.low_stock_count || 0}</p>
            </div>
            <div className="bg-red-200 rounded-full p-3">
              <AlertTriangle className="w-8 h-8 text-red-700" />
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl p-6 border border-emerald-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-emerald-800">มูลค่าสต๊อก</p>
              <p className="text-3xl font-bold text-emerald-900 mt-2">
                ฿{(stats?.total_stock_value || 0).toLocaleString()}
              </p>
            </div>
            <div className="bg-emerald-200 rounded-full p-3">
              <DollarSign className="w-8 h-8 text-emerald-700" />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-amber-600" />
          ธุรกรรมล่าสุด
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">วันที่</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">สินค้า</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">ประเภท</th>
                <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">จำนวน</th>
              </tr>
            </thead>
            <tbody>
              {stats?.recent_transactions.slice(0, 8).map((trans) => (
                <tr key={trans.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {new Date(trans.transaction_date).toLocaleDateString('th-TH', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-900">{trans.product_name}</td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                      trans.transaction_type === 'in' 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {trans.transaction_type === 'in' ? (
                        <>
                          <ArrowUpCircle className="w-3 h-3" />
                          รับเข้า
                        </>
                      ) : (
                        <>
                          <ArrowDownCircle className="w-3 h-3" />
                          จ่ายออก
                        </>
                      )}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right text-sm font-medium text-gray-900">
                    {trans.quantity.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Products Component
const ProductsPage = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  useEffect(() => {
    loadProducts();
  }, [searchTerm]);

  const loadProducts = async () => {
    try {
      const data = await apiCall(`/api/products${searchTerm ? `?search=${searchTerm}` : ''}`);
      setProducts(data);
    } catch (error) {
      console.error('Error loading products:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteProduct = async (id) => {
    if (!confirm('ต้องการลบสินค้านี้?')) return;
    
    try {
      await apiCall(`/api/products/${id}`, { method: 'DELETE' });
      loadProducts();
    } catch (error) {
      alert('Error deleting product: ' + error.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">จัดการสินค้า</h2>
        <button
          onClick={() => { setSelectedProduct(null); setShowAddModal(true); }}
          className="flex items-center gap-2 bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          <Plus className="w-5 h-5" />
          เพิ่มสินค้า
        </button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="ค้นหาสินค้า (รหัส, ชื่อ, หมวดหมู่)"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
        />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">รหัส</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">ชื่อสินค้า</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">หมวดหมู่</th>
                <th className="text-right py-4 px-6 text-sm font-semibold text-gray-700">สต๊อก</th>
                <th className="text-right py-4 px-6 text-sm font-semibold text-gray-700">ราคา/หน่วย</th>
                <th className="text-center py-4 px-6 text-sm font-semibold text-gray-700">จัดการ</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="py-4 px-6 text-sm font-medium text-gray-900">{product.code}</td>
                  <td className="py-4 px-6 text-sm text-gray-900">{product.name}</td>
                  <td className="py-4 px-6">
                    <span className="inline-block px-3 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
                      {product.category}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-right text-sm font-semibold text-gray-900">
                    {product.current_stock} {product.unit}
                  </td>
                  <td className="py-4 px-6 text-right text-sm text-gray-900">
                    ฿{product.unit_cost.toLocaleString()}
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center justify-center gap-2">
                      <button
                        onClick={() => { setSelectedProduct(product); setShowAddModal(true); }}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        title="แก้ไข"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => deleteProduct(product.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="ลบ"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showAddModal && (
        <ProductModal
          product={selectedProduct}
          onClose={() => { setShowAddModal(false); setSelectedProduct(null); }}
          onSave={() => { loadProducts(); setShowAddModal(false); setSelectedProduct(null); }}
        />
      )}
    </div>
  );
};

// Product Modal
const ProductModal = ({ product, onClose, onSave }) => {
  const [formData, setFormData] = useState(product || {
    code: '',
    name: '',
    category: 'Whiskey',
    unit: 'ขวด',
    unit_cost: 0,
    ordering_cost: 500,
    holding_cost_percentage: 0.2,
    lead_time_days: 7,
    current_stock: 0
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (product) {
        await apiCall(`/api/products/${product.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
      } else {
        await apiCall('/api/products', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
      }
      onSave();
    } catch (error) {
      alert('Error: ' + error.message);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-xl font-bold text-gray-900">
            {product ? 'แก้ไขสินค้า' : 'เพิ่มสินค้าใหม่'}
          </h3>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">รหัสสินค้า</label>
              <input
                type="text"
                required
                disabled={!!product}
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">หมวดหมู่</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
              >
                <option value="Whiskey">Whiskey</option>
                <option value="Vodka">Vodka</option>
                <option value="Rum">Rum</option>
                <option value="Beer">Beer</option>
                <option value="Wine">Wine</option>
                <option value="Gin">Gin</option>
                <option value="Liqueur">Liqueur</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">ชื่อสินค้า</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">หน่วยนับ</label>
              <input
                type="text"
                value={formData.unit}
                onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">ราคาต่อหน่วย (฿)</label>
              <input
                type="number"
                required
                step="0.01"
                value={formData.unit_cost}
                onChange={(e) => setFormData({ ...formData, unit_cost: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">สต๊อกปัจจุบัน</label>
              <input
                type="number"
                value={formData.current_stock}
                onChange={(e) => setFormData({ ...formData, current_stock: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">ต้นทุนการสั่งซื้อ (฿)</label>
              <input
                type="number"
                step="0.01"
                value={formData.ordering_cost}
                onChange={(e) => setFormData({ ...formData, ordering_cost: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">% ต้นทุนเก็บรักษา</label>
              <input
                type="number"
                step="0.01"
                value={formData.holding_cost_percentage}
                onChange={(e) => setFormData({ ...formData, holding_cost_percentage: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Lead Time (วัน)</label>
              <input
                type="number"
                value={formData.lead_time_days}
                onChange={(e) => setFormData({ ...formData, lead_time_days: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              className="flex-1 bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              บันทึก
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-lg font-medium transition-colors"
            >
              ยกเลิก
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Transactions Component
const TransactionsPage = () => {
  const [products, setProducts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    loadProducts();
    loadTransactions();
  }, [selectedProduct]);

  const loadProducts = async () => {
    const data = await apiCall('/api/products');
    setProducts(data);
  };

  const loadTransactions = async () => {
    const endpoint = selectedProduct 
      ? `/api/transactions?product_id=${selectedProduct}`
      : '/api/transactions';
    const data = await apiCall(endpoint);
    setTransactions(data);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">ธุรกรรมสินค้า</h2>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          <Plus className="w-5 h-5" />
          บันทึกธุรกรรม
        </button>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">กรองตามสินค้า</label>
        <select
          value={selectedProduct}
          onChange={(e) => setSelectedProduct(e.target.value)}
          className="w-full md:w-96 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
        >
          <option value="">ทั้งหมด</option>
          {products.map(p => (
            <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
          ))}
        </select>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">วันที่/เวลา</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">สินค้า</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">ประเภท</th>
                <th className="text-right py-4 px-6 text-sm font-semibold text-gray-700">จำนวน</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">หมายเหตุ</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((trans) => (
                <tr key={trans.id} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="py-4 px-6 text-sm text-gray-600">
                    {new Date(trans.transaction_date).toLocaleString('th-TH')}
                  </td>
                  <td className="py-4 px-6 text-sm text-gray-900">
                    {trans.product_code} - {trans.product_name}
                  </td>
                  <td className="py-4 px-6">
                    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${
                      trans.transaction_type === 'in' 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {trans.transaction_type === 'in' ? (
                        <>
                          <ArrowUpCircle className="w-3 h-3" />
                          รับเข้า
                        </>
                      ) : (
                        <>
                          <ArrowDownCircle className="w-3 h-3" />
                          จ่ายออก
                        </>
                      )}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-right text-sm font-semibold text-gray-900">
                    {trans.quantity.toLocaleString()}
                  </td>
                  <td className="py-4 px-6 text-sm text-gray-600">{trans.note || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showAddModal && (
        <TransactionModal
          products={products}
          onClose={() => setShowAddModal(false)}
          onSave={() => { loadTransactions(); loadProducts(); setShowAddModal(false); }}
        />
      )}
    </div>
  );
};

// Transaction Modal
const TransactionModal = ({ products, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    product_id: '',
    transaction_type: 'in',
    quantity: 0,
    note: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await apiCall('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      onSave();
    } catch (error) {
      alert('Error: ' + error.message);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-md w-full">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-xl font-bold text-gray-900">บันทึกธุรกรรม</h3>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">เลือกสินค้า</label>
            <select
              required
              value={formData.product_id}
              onChange={(e) => setFormData({ ...formData, product_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
            >
              <option value="">-- เลือกสินค้า --</option>
              {products.map(p => (
                <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">ประเภท</label>
            <select
              value={formData.transaction_type}
              onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
            >
              <option value="in">รับเข้า</option>
              <option value="out">จ่ายออก</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">จำนวน</label>
            <input
              type="number"
              required
              min="1"
              value={formData.quantity}
              onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">หมายเหตุ</label>
            <textarea
              value={formData.note}
              onChange={(e) => setFormData({ ...formData, note: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              className="flex-1 bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              บันทึก
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-lg font-medium transition-colors"
            >
              ยกเลิก
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Forecasting Component
const ForecastingPage = () => {
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [periods, setPeriods] = useState(30);

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    const data = await apiCall('/api/products');
    setProducts(data);
  };

  const loadForecast = async () => {
    if (!selectedProduct) return;
    
    setLoading(true);
    try {
      const data = await apiCall(`/api/forecast/${selectedProduct}?periods=${periods}`);
      setForecastData(data);
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const chartData = forecastData ? forecastData.forecast.dates.map((date, idx) => ({
    date: new Date(date).toLocaleDateString('th-TH', { month: 'short', day: 'numeric' }),
    forecast: Math.round(forecastData.forecast.values[idx]),
    lower: Math.round(forecastData.forecast.confidence_intervals[idx][0]),
    upper: Math.round(forecastData.forecast.confidence_intervals[idx][1])
  })) : [];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">การพยากรณ์ความต้องการ</h2>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">เลือกสินค้า</label>
            <select
              value={selectedProduct}
              onChange={(e) => setSelectedProduct(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
            >
              <option value="">-- เลือกสินค้า --</option>
              {products.map(p => (
                <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">ระยะพยากรณ์ (วัน)</label>
            <input
              type="number"
              min="7"
              max="90"
              value={periods}
              onChange={(e) => setPeriods(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
            />
          </div>
        </div>

        <button
          onClick={loadForecast}
          disabled={!selectedProduct || loading}
          className="w-full bg-amber-600 hover:bg-amber-700 disabled:bg-gray-300 text-white px-4 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              กำลังคำนวณ...
            </>
          ) : (
            <>
              <TrendingUp className="w-5 h-5" />
              พยากรณ์
            </>
          )}
        </button>
      </div>

      {forecastData && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
              <p className="text-sm font-medium text-blue-800">EOQ (ปริมาณสั่งซื้อที่เหมาะสม)</p>
              <p className="text-3xl font-bold text-blue-900 mt-2">
                {forecastData.metrics.eoq.toLocaleString()}
              </p>
              <p className="text-xs text-blue-700 mt-1">{forecastData.product.unit}</p>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-200">
              <p className="text-sm font-medium text-purple-800">Safety Stock</p>
              <p className="text-3xl font-bold text-purple-900 mt-2">
                {forecastData.metrics.safety_stock.toLocaleString()}
              </p>
              <p className="text-xs text-purple-700 mt-1">{forecastData.product.unit}</p>
            </div>

            <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-xl p-6 border border-orange-200">
              <p className="text-sm font-medium text-orange-800">Reorder Point</p>
              <p className="text-3xl font-bold text-orange-900 mt-2">
                {forecastData.metrics.reorder_point.toLocaleString()}
              </p>
              <p className="text-xs text-orange-700 mt-1">{forecastData.product.unit}</p>
            </div>

            <div className={`bg-gradient-to-br rounded-xl p-6 border ${
              forecastData.metrics.stock_status === 'ต้องสั่งซื้อ'
                ? 'from-red-50 to-rose-50 border-red-200'
                : 'from-green-50 to-emerald-50 border-green-200'
            }`}>
              <p className={`text-sm font-medium ${
                forecastData.metrics.stock_status === 'ต้องสั่งซื้อ'
                  ? 'text-red-800'
                  : 'text-green-800'
              }`}>สถานะสต๊อก</p>
              <p className={`text-3xl font-bold mt-2 ${
                forecastData.metrics.stock_status === 'ต้องสั่งซื้อ'
                  ? 'text-red-900'
                  : 'text-green-900'
              }`}>
                {forecastData.metrics.current_stock}
              </p>
              <p className={`text-xs mt-1 ${
                forecastData.metrics.stock_status === 'ต้องสั่งซื้อ'
                  ? 'text-red-700'
                  : 'text-green-700'
              }`}>{forecastData.metrics.stock_status}</p>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="mb-4">
              <h3 className="text-lg font-bold text-gray-900">กราฟการพยากรณ์</h3>
              <p className="text-sm text-gray-600">
                ARIMA({forecastData.forecast.arima_params.p}, {forecastData.forecast.arima_params.d}, {forecastData.forecast.arima_params.q})
              </p>
            </div>
            
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="date" 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="upper" 
                  stackId="1"
                  stroke="none"
                  fill="#fef3c7"
                  fillOpacity={0.6}
                  name="ช่วงความเชื่อมั่นบน"
                />
                <Area 
                  type="monotone" 
                  dataKey="forecast" 
                  stroke="#f59e0b"
                  strokeWidth={3}
                  fill="url(#colorForecast)"
                  name="พยากรณ์"
                />
                <Area 
                  type="monotone" 
                  dataKey="lower" 
                  stackId="2"
                  stroke="none"
                  fill="#fef3c7"
                  fillOpacity={0.6}
                  name="ช่วงความเชื่อมั่นล่าง"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">สถิติและตัวชี้วัด</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-gray-600">ความต้องการเฉลี่ยต่อวัน</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {forecastData.metrics.avg_daily_demand.toFixed(2)} {forecastData.product.unit}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">ความต้องการต่อปี (ประมาณ)</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {Math.round(forecastData.metrics.annual_demand).toLocaleString()} {forecastData.product.unit}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">ส่วนเบี่ยงเบนมาตรฐาน</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {forecastData.metrics.demand_std.toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// Sales Upload Component
const SalesUploadPage = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_URL}/api/sales/upload`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
      }

      const result = await response.json();
      setUploadResult({ success: true, message: result.message });
    } catch (error) {
      setUploadResult({ success: false, message: error.message });
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = () => {
    const csv = 'product_code,date,quantity\nWHI001,2024-01-01,25\nVOD001,2024-01-01,30\n';
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sales_template.csv';
    a.click();
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">นำเข้าข้อมูลยอดขาย</h2>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8">
            <Upload className="w-16 h-16 text-amber-600 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-gray-900 mb-2">อัพโหลดไฟล์ CSV</h3>
            <p className="text-gray-600">
              ไฟล์ต้องมีคอลัมน์: product_code, date, quantity
            </p>
          </div>

          <div className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-amber-500 transition-colors">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileUpload}
                disabled={uploading}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer inline-flex items-center gap-2 bg-amber-600 hover:bg-amber-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                {uploading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    กำลังอัพโหลด...
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5" />
                    เลือกไฟล์
                  </>
                )}
              </label>
            </div>

            <button
              onClick={downloadTemplate}
              className="w-full flex items-center justify-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-800 px-4 py-3 rounded-lg font-medium transition-colors"
            >
              <Download className="w-5 h-5" />
              ดาวน์โหลดไฟล์ตัวอย่าง
            </button>

            {uploadResult && (
              <div className={`p-4 rounded-lg ${
                uploadResult.success 
                  ? 'bg-green-50 text-green-800 border border-green-200' 
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}>
                <p className="font-medium">{uploadResult.message}</p>
              </div>
            )}
          </div>

          <div className="mt-8 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <h4 className="font-semibold text-amber-900 mb-2">รูปแบบไฟล์ CSV:</h4>
            <pre className="text-sm text-amber-800 bg-white p-3 rounded border border-amber-200 overflow-x-auto">
{`product_code,date,quantity
WHI001,2024-01-01,25
VOD001,2024-01-01,30
BEE001,2024-01-02,85`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [currentPage, setCurrentPage] = useState('dashboard');

  const pages = {
    dashboard: { title: 'แดชบอร์ด', icon: Activity, component: Dashboard },
    products: { title: 'จัดการสินค้า', icon: Package, component: ProductsPage },
    transactions: { title: 'ธุรกรรม', icon: ArrowUpCircle, component: TransactionsPage },
    forecast: { title: 'พยากรณ์', icon: TrendingUp, component: ForecastingPage },
    upload: { title: 'นำเข้าข้อมูล', icon: Upload, component: SalesUploadPage }
  };

  const CurrentComponent = pages[currentPage].component;

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-amber-600 to-orange-600 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3">
            <Boxes className="w-10 h-10 text-white" />
            <div>
              <h1 className="text-3xl font-bold text-white">
                ระบบจัดการสต๊อกและคาดการณ์สินค้า
              </h1>
              <p className="text-amber-100 text-sm mt-1">
                Inventory Forecasting System with ARIMA
              </p>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar */}
          <aside className="lg:w-64 flex-shrink-0">
            <nav className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 space-y-1">
              {Object.entries(pages).map(([key, page]) => {
                const Icon = page.icon;
                const isActive = currentPage === key;
                return (
                  <button
                    key={key}
                    onClick={() => setCurrentPage(key)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all ${
                      isActive
                        ? 'bg-amber-100 text-amber-900 shadow-sm'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className={`w-5 h-5 ${isActive ? 'text-amber-600' : 'text-gray-500'}`} />
                    {page.title}
                  </button>
                );
              })}
            </nav>
          </aside>

          {/* Main Content */}
          <main className="flex-1 min-w-0">
            <CurrentComponent onNavigate={setCurrentPage} />
          </main>
        </div>
      </div>
    </div>
  );
};

export default App;