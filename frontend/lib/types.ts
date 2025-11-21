export interface Paper {
  id: string;              // ← bắt buộc
  title: string;           // ← bắt buộc
  abstract: string;        // ← bắt buộc
  authors?: string[];
  pdf_url?: string;
  keywords?: string[];
  citations_by_year?: Record<string, number>;
}
