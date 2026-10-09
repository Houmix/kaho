export type PaymentMethod = 'STRIPE' | 'CASH' | 'CHECK' | 'TRANSFER' | 'CPF' | 'FREE';
export const PAYMENT_METHODS: { key: PaymentMethod; label: string }[] = [
  { key: 'CASH', label: 'Espèces' }, { key: 'CHECK', label: 'Chèque' }, { key: 'TRANSFER', label: 'Virement' }, { key: 'CPF', label: 'CPF' }, { key: 'STRIPE', label: 'Carte (terminal / lien)' },
];

export type OfferCategory = 'PERMIS_B' | 'CODE' | 'PERFECTIONNEMENT' | 'RECHARGE';

export interface Offer {
  id: number;
  name: string;
  description: string;
  category: OfferCategory;
  category_display: string;
  hours: number;
  price: string;
  price_per_hour: number | null;
  billing_type: 'ONE_TIME' | 'MONTHLY' | 'INSTALLMENTS_3' | 'INSTALLMENTS_4';
  billing_display: string;
  includes_lms: boolean;
  validity_months: number | null;
  for_code_status: 'ANY' | 'TO_PASS' | 'OBTAINED';
  for_level: 'ANY' | 'BEGINNER' | 'REFRESH';
  gearbox: 'ANY' | 'AUTO' | 'MANUAL';
  is_featured: boolean;
}

export interface Package {
  id: number;
  offer: number | null;
  offer_name: string | null;
  offer_category: OfferCategory | null;
  includes_lms: boolean;
  hours_purchased: number;
  amount_paid: string;
  status: 'PENDING' | 'COMPLETED' | 'FAILED';
  status_display: string;
  label: string;
  display_label: string;
  payment_method: PaymentMethod | '';
  payment_method_display: string;
  stripe_checkout_url: string;
  paid_at: string | null;
  note?: string;
  expires_at: string | null;
  invoice_id: number | null;
  invoice_number: string | null;
  created_at: string;
}

export const CATEGORY_LABELS: Record<OfferCategory, string> = {
  PERMIS_B: 'Permis B',
  CODE: 'Code seul',
  PERFECTIONNEMENT: 'Perfectionnement',
  RECHARGE: "Recharge d'heures",
};

export function formatPrice(value: string | number): string {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(Number(value));
}

export function billingSuffix(o: Offer): string {
  switch (o.billing_type) {
    case 'MONTHLY': return '/ mois';
    case 'INSTALLMENTS_3': return `soit 3 × ${formatPrice(Number(o.price) / 3)}`;
    case 'INSTALLMENTS_4': return `soit 4 × ${formatPrice(Number(o.price) / 4)}`;
    default: return '';
  }
}

export function offerHighlights(o: Offer): string[] {
  const h: string[] = [];
  if (o.hours > 0) h.push(`${o.hours} h de conduite`);
  if (o.includes_lms) h.push('Cours de code, quiz et examens blancs');
  h.push(o.validity_months ? `Valable ${o.validity_months} mois` : 'Sans limite de durée');
  if (o.gearbox !== 'ANY') h.push(o.gearbox === 'AUTO' ? 'Boîte automatique' : 'Boîte manuelle');
  return h;
}

export interface OfferAdmin extends Offer { is_active: boolean; display_order: number; sales: number; created_at: string }
export const BILLING_LABELS = { ONE_TIME: 'Paiement unique', MONTHLY: 'Abonnement mensuel', INSTALLMENTS_3: 'En 3 fois', INSTALLMENTS_4: 'En 4 fois' };
