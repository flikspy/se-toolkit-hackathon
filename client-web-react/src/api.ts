import { GroceryItem, GroceryItemInput } from './types';

const API_URL = process.env.REACT_APP_API_URL || (process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000');

export async function fetchItems(): Promise<GroceryItem[]> {
  const res = await fetch(`${API_URL}/items`);
  if (!res.ok) throw new Error('Failed to fetch items');
  return res.json();
}

export async function createItem(item: GroceryItemInput): Promise<GroceryItem> {
  const res = await fetch(`${API_URL}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item),
  });
  if (!res.ok) throw new Error('Failed to create item');
  return res.json();
}

export async function toggleItem(id: number): Promise<GroceryItem> {
  const res = await fetch(`${API_URL}/items/${id}/toggle`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to toggle item');
  return res.json();
}

export async function deleteItem(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/items/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete item');
}

export async function addViaAgent(text: string): Promise<GroceryItem[]> {
  const res = await fetch(`${API_URL}/agent/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error('Failed to process agent input');
  return res.json();
}
