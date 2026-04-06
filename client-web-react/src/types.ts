export interface GroceryItem {
  id: number;
  name: string;
  quantity: string;
  category: string;
  is_bought: boolean;
  created_at: string;
  updated_at: string;
}

export interface GroceryItemInput {
  name: string;
  quantity?: string;
  category?: string;
}
