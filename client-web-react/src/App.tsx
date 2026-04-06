import { useState, useEffect } from 'react';
import { fetchItems, createItem, toggleItem, deleteItem, addViaAgent } from './api';
import { GroceryItem } from './types';
import './App.css';

function App() {
  const [items, setItems] = useState<GroceryItem[]>([]);
  const [newItemName, setNewItemName] = useState('');
  const [newItemQty, setNewItemQty] = useState('1');
  const [agentInput, setAgentInput] = useState('');
  const [showAgent, setShowAgent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadItems = async () => {
    try {
      const data = await fetchItems();
      setItems(data);
      setError(null);
    } catch {
      setError('Failed to load items');
    }
  };

  useEffect(() => {
    loadItems();
    const interval = setInterval(loadItems, 5000); // Auto-refresh every 5s
    return () => clearInterval(interval);
  }, []);

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newItemName.trim()) return;
    setLoading(true);
    try {
      await createItem({ name: newItemName.trim(), quantity: newItemQty });
      setNewItemName('');
      setNewItemQty('1');
      await loadItems();
    } catch {
      setError('Failed to add item');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (id: number) => {
    try {
      await toggleItem(id);
      await loadItems();
    } catch {
      setError('Failed to update item');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteItem(id);
      await loadItems();
    } catch {
      setError('Failed to delete item');
    }
  };

  const handleAgentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agentInput.trim()) return;
    setLoading(true);
    try {
      await addViaAgent(agentInput);
      setAgentInput('');
      setShowAgent(false);
      await loadItems();
    } catch {
      setError('Failed to process agent input');
    } finally {
      setLoading(false);
    }
  };

  const pendingItems = items.filter(i => !i.is_bought);
  const boughtItems = items.filter(i => i.is_bought);

  return (
    <div className="app">
      <header className="app-header">
        <h1>🛒 Shared Grocery List</h1>
        <button className="agent-btn" onClick={() => setShowAgent(!showAgent)}>
          🤖 AI Add
        </button>
      </header>

      {showAgent && (
        <form onSubmit={handleAgentSubmit} className="agent-form">
          <input
            type="text"
            value={agentInput}
            onChange={e => setAgentInput(e.target.value)}
            placeholder='e.g. "add milk and eggs"'
          />
          <button type="submit" disabled={loading}>Add via AI</button>
        </form>
      )}

      <form onSubmit={handleAddItem} className="add-form">
        <input
          type="text"
          value={newItemName}
          onChange={e => setNewItemName(e.target.value)}
          placeholder="Item name"
          required
        />
        <input
          type="text"
          value={newItemQty}
          onChange={e => setNewItemQty(e.target.value)}
          placeholder="Qty"
          style={{ width: '60px' }}
        />
        <button type="submit" disabled={loading}>Add</button>
      </form>

      {error && <div className="error">{error}</div>}

      <div className="item-list">
        <h2>To Buy ({pendingItems.length})</h2>
        {pendingItems.length === 0 && <p className="empty">All done! 🎉</p>}
        {pendingItems.map(item => (
          <div key={item.id} className="item">
            <div className="item-info" onClick={() => handleToggle(item.id)}>
              <span className="item-name">{item.name}</span>
              <span className="item-qty">×{item.quantity}</span>
            </div>
            <button className="delete-btn" onClick={() => handleDelete(item.id)}>✕</button>
          </div>
        ))}
      </div>

      {boughtItems.length > 0 && (
        <div className="item-list bought">
          <h2>Bought ({boughtItems.length})</h2>
          {boughtItems.map(item => (
            <div key={item.id} className="item bought" onClick={() => handleToggle(item.id)}>
              <div className="item-info">
                <span className="item-name">{item.name}</span>
                <span className="item-qty">×{item.quantity}</span>
              </div>
              <button className="delete-btn" onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }}>✕</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;
