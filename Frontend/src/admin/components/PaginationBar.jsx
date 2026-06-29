import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

export default function PaginationBar({ page, totalPages, totalElements, onPageChange, loading }) {
  return (
    <div className="admin-pagination-bar">
      <span className="admin-pagination-info">
        {totalElements != null ? `${totalElements.toLocaleString()} total` : ""}
      </span>
      <div className="admin-pagination-controls">
        <button
          className="admin-pag-btn"
          disabled={page === 0 || loading}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft size={16} />
        </button>
        <span className="admin-pag-current">Page {page + 1} of {totalPages || 1}</span>
        <button
          className="admin-pag-btn"
          disabled={page + 1 >= totalPages || loading}
          onClick={() => onPageChange(page + 1)}
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}