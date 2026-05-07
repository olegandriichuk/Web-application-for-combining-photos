// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

export type PhotoItem = {
  id: string;
  original_name: string;
  mime: string;
  size: number;
  created_at: string;
  preview_url: string | null;
  original_width: number | null;
  original_height: number | null;
};
