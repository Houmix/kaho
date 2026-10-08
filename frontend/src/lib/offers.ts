export interface Offer {
  id: number;
  name: string;
  description: string;
  hours: number;
  price: string;
  price_per_hour: number;
  is_featured: boolean;
}

export interface Package {
  id: number;
  offer: number | null;
  offer_name: string | null;
  hours_purchased: number;
  amount_paid: string;
  status: 'PENDING' | 'COMPLETED' | 'FAILED';
  status_display: string;
  created_at: string;
}

export function formatPrice(value: string | number): string {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(Number(value));
}
