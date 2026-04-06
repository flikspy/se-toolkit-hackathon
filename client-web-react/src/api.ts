import { GroceryItem, GroceryItemInput } from './types';

const API_URL = process.env.REACT_APP_API_URL || (process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000');

export interface Room {
  id: number;
  code: string;
  created_at: string;
}

export async function createRoom(): Promise<Room> {
  const res = await fetch(`${API_URL}/rooms`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to create room');
  return res.json();
}

export async function joinRoom(code: string): Promise<Room> {
  const res = await fetch(`${API_URL}/rooms/${code.toUpperCase()}`);
  if (!res.ok) throw new Error('Room not found');
  return res.json();
}

export async function fetchItems(roomCode: string): Promise<GroceryItem[]> {
  const res = await fetch(`${API_URL}/rooms/${roomCode}/items`);
  if (!res.ok) throw new Error('Failed to fetch items');
  return res.json();
}

export async function createItem(roomCode: string, item: GroceryItemInput): Promise<GroceryItem> {
  const res = await fetch(`${API_URL}/rooms/${roomCode}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item),
  });
  if (!res.ok) throw new Error('Failed to create item');
  return res.json();
}

export async function toggleItem(roomCode: string, id: number): Promise<GroceryItem> {
  const res = await fetch(`${API_URL}/rooms/${roomCode}/items/${id}/toggle`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to toggle item');
  return res.json();
}

export async function deleteItem(roomCode: string, id: number): Promise<void> {
  const res = await fetch(`${API_URL}/rooms/${roomCode}/items/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete item');
}

export async function addViaAgent(text: string, roomCode: string): Promise<GroceryItem[]> {
  const res = await fetch(`${API_URL}/agent/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, room_code: roomCode }),
  });
  if (!res.ok) throw new Error('Failed to process agent input');
  return res.json();
}
