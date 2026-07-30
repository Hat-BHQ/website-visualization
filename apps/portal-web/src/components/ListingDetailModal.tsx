import { useEffect } from 'react';

import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingScreen } from '@/components/LoadingScreen';

import type {
    ListingDetailResponse,
    ListingSnapshotItem,
} from '@/types/hqa';

interface ListingDetailModalProps {
    open: boolean;
    detail?: ListingDetailResponse;
    history?: ListingSnapshotItem[];

    detailLoading: boolean;
    historyLoading: boolean;

    detailError: boolean;
    historyError: boolean;

    onClose: () => void;
    onRetryDetail: () => void;
    onRetryHistory: () => void;
}

function formatDateTime(value: string | null | undefined) {
    if (!value) {
        return 'N/A';
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString('vi-VN');
}

function displayValue(
    value: string | number | null | undefined,
) {
    if (
        value === null ||
        value === undefined ||
        value === ''
    ) {
        return 'N/A';
    }

    return String(value);
}

function DetailField({
    label,
    value,
}: {
    label: string;
    value: React.ReactNode;
}) {
    return (
        <div className="listing-detail-field">
            <span className="listing-detail-label">
                {label}
            </span>

            <div className="listing-detail-value">
                {value}
            </div>
        </div>
    );
}

export function ListingDetailModal({
    open,
    detail,
    history,
    detailLoading,
    historyLoading,
    detailError,
    historyError,
    onClose,
    onRetryDetail,
    onRetryHistory,
}: ListingDetailModalProps) {
    /**
     * Khi mở popup:
     * - Khóa scroll của trang phía sau.
     * - Cho phép đóng bằng phím Escape.
     */
    useEffect(() => {
        if (!open) {
            return undefined;
        }

        const previousOverflow =
            document.body.style.overflow;

        document.body.style.overflow = 'hidden';

        const handleKeyDown = (
            event: KeyboardEvent,
        ) => {
            if (event.key === 'Escape') {
                onClose();
            }
        };

        window.addEventListener(
            'keydown',
            handleKeyDown,
        );

        return () => {
            document.body.style.overflow =
                previousOverflow;

            window.removeEventListener(
                'keydown',
                handleKeyDown,
            );
        };
    }, [open, onClose]);

    if (!open) {
        return null;
    }

    return (
        <div
            className="modal-backdrop"
            role="presentation"
            onMouseDown={(event) => {
                // Chỉ đóng khi click trực tiếp vào nền mờ.
                // Click bên trong popup sẽ không đóng.
                if (event.target === event.currentTarget) {
                    onClose();
                }
            }}
        >
            <section
                className="modal-panel modal-panel--listing"
                role="dialog"
                aria-modal="true"
                aria-labelledby="listing-detail-title"
            >
                <header className="modal-header">
                    <div>
                        <h2
                            id="listing-detail-title"
                            className="modal-title"
                        >
                            Chi tiết sản phẩm
                        </h2>

                        <p className="modal-subtitle">
                            Thông tin listing và lịch sử thay đổi
                        </p>
                    </div>

                    <button
                        type="button"
                        className="modal-close-button"
                        aria-label="Đóng popup"
                        onClick={onClose}
                    >
                        ×
                    </button>
                </header>

                <div className="modal-body">
                    {detailLoading ? (
                        <LoadingScreen label="Đang tải chi tiết sản phẩm..." />
                    ) : null}

                    {detailError ? (
                        <ErrorState
                            title="Không thể tải chi tiết"
                            message="Vui lòng thử lại."
                            action={
                                <button
                                    className="action-button"
                                    type="button"
                                    onClick={onRetryDetail}
                                >
                                    Thử lại
                                </button>
                            }
                        />
                    ) : null}

                    {detail ? (
                        <>
                            <div className="listing-detail-layout">
                                {detail.image_url ? (
                                    <div className="listing-detail-image-wrap">
                                        <img
                                            className="listing-detail-image"
                                            src={detail.image_url}
                                            alt={detail.listing_title}
                                        />
                                    </div>
                                ) : null}

                                <div className="listing-detail-grid">
                                    <DetailField
                                        label="Tên sản phẩm"
                                        value={detail.listing_title}
                                    />

                                    <DetailField
                                        label="Listing ID"
                                        value={
                                            detail.external_listing_id
                                        }
                                    />

                                    <DetailField
                                        label="Người bán"
                                        value={
                                            detail.seller_name ??
                                            detail.shop_name ??
                                            'N/A'
                                        }
                                    />

                                    <DetailField
                                        label="Giá hiện tại"
                                        value={
                                            detail.current_price
                                                ? `${detail.current_price} ${detail.currency ?? ''
                                                }`
                                                : 'N/A'
                                        }
                                    />

                                    <DetailField
                                        label="Phí vận chuyển"
                                        value={
                                            detail.shipping_price
                                                ? `${detail.shipping_price} ${detail.currency ?? ''
                                                }`
                                                : 'N/A'
                                        }
                                    />

                                    <DetailField
                                        label="Tổng giá"
                                        value={
                                            detail.total_price
                                                ? `${detail.total_price} ${detail.currency ?? ''
                                                }`
                                                : 'N/A'
                                        }
                                    />

                                    <DetailField
                                        label="Trạng thái"
                                        value={detail.listing_status}
                                    />

                                    <DetailField
                                        label="Lý do trạng thái"
                                        value={displayValue(
                                            detail.status_reason,
                                        )}
                                    />

                                    <DetailField
                                        label="Danh mục"
                                        value={displayValue(
                                            detail.category_name,
                                        )}
                                    />

                                    <DetailField
                                        label="Tình trạng"
                                        value={displayValue(
                                            detail.condition_name,
                                        )}
                                    />

                                    <DetailField
                                        label="Vị trí"
                                        value={displayValue(
                                            detail.listing_location,
                                        )}
                                    />

                                    <DetailField
                                        label="Lượt xem"
                                        value={displayValue(
                                            detail.listing_views,
                                        )}
                                    />

                                    <DetailField
                                        label="Ngày đăng"
                                        value={formatDateTime(
                                            detail.published_at,
                                        )}
                                    />

                                    <DetailField
                                        label="Lần đầu ghi nhận"
                                        value={formatDateTime(
                                            detail.first_seen_at,
                                        )}
                                    />

                                    <DetailField
                                        label="Cập nhật gần nhất"
                                        value={formatDateTime(
                                            detail.last_seen_at,
                                        )}
                                    />

                                    <DetailField
                                        label="Marketplace URL"
                                        value={
                                            <a
                                                href={detail.listing_url}
                                                target="_blank"
                                                rel="noreferrer"
                                            >
                                                Mở sản phẩm
                                            </a>
                                        }
                                    />
                                </div>
                            </div>

                            <section className="listing-history-section">
                                <h3>Lịch sử thay đổi</h3>

                                {historyLoading ? (
                                    <LoadingScreen label="Đang tải lịch sử..." />
                                ) : null}

                                {historyError ? (
                                    <ErrorState
                                        title="Không thể tải lịch sử"
                                        message="Vui lòng thử lại."
                                        action={
                                            <button
                                                className="action-button"
                                                type="button"
                                                onClick={onRetryHistory}
                                            >
                                                Thử lại
                                            </button>
                                        }
                                    />
                                ) : null}

                                {history &&
                                    history.length === 0 ? (
                                    <EmptyState
                                        title="Không có lịch sử"
                                        message="Listing chưa có snapshot."
                                    />
                                ) : null}

                                {history &&
                                    history.length > 0 ? (
                                    <div className="table-scroll">
                                        <table className="data-table">
                                            <thead>
                                                <tr>
                                                    <th>Thời điểm</th>
                                                    <th>Giá</th>
                                                    <th>Phí vận chuyển</th>
                                                    <th>Tổng giá</th>
                                                    <th>Trạng thái</th>
                                                    <th>Lượt xem</th>
                                                </tr>
                                            </thead>

                                            <tbody>
                                                {history.map((item) => (
                                                    <tr key={item.id}>
                                                        <td>
                                                            {formatDateTime(
                                                                item.observed_at,
                                                            )}
                                                        </td>

                                                        <td>
                                                            {displayValue(
                                                                item.price,
                                                            )}
                                                        </td>

                                                        <td>
                                                            {displayValue(
                                                                item.shipping_price,
                                                            )}
                                                        </td>

                                                        <td>
                                                            {displayValue(
                                                                item.total_price,
                                                            )}
                                                        </td>

                                                        <td>
                                                            {displayValue(
                                                                item.listing_status,
                                                            )}
                                                        </td>

                                                        <td>
                                                            {displayValue(
                                                                item.listing_views,
                                                            )}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                ) : null}
                            </section>
                        </>
                    ) : null}
                </div>
            </section>
        </div>
    );
}