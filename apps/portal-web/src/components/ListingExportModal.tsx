import {
    useEffect,
    useMemo,
    useState,
} from 'react';

import {
    exportMarketplaceListings,
} from '@/api/hqa';

import type {
    ListingExportFormat,
    ListingListParams,
    Marketplace,
} from '@/types/hqa';

interface ExportFieldOption {
    key: string;
    label: string;
}

const EXPORT_FIELDS: ExportFieldOption[] = [
    { key: 'id', label: 'ID nội bộ' },
    {
        key: 'external_listing_id',
        label: 'Listing ID',
    },
    {
        key: 'listing_title',
        label: 'Tên sản phẩm',
    },
    {
        key: 'listing_url',
        label: 'Listing URL',
    },
    {
        key: 'seller',
        label: 'Người bán / Shop',
    },
    { key: 'shop_id', label: 'Shop ID' },
    {
        key: 'published_at',
        label: 'Ngày đăng',
    },
    {
        key: 'listing_location',
        label: 'Vị trí',
    },
    {
        key: 'country_code',
        label: 'Mã quốc gia',
    },
    {
        key: 'category_id',
        label: 'Category ID',
    },
    {
        key: 'category_name',
        label: 'Danh mục',
    },
    {
        key: 'condition_id',
        label: 'Condition ID',
    },
    {
        key: 'condition_name',
        label: 'Tình trạng',
    },
    {
        key: 'image_url',
        label: 'Image URL',
    },
    {
        key: 'current_price',
        label: 'Giá hiện tại',
    },
    {
        key: 'shipping_price',
        label: 'Phí vận chuyển',
    },
    {
        key: 'total_price',
        label: 'Tổng giá',
    },
    {
        key: 'currency',
        label: 'Tiền tệ',
    },
    {
        key: 'listing_views',
        label: 'Lượt xem',
    },
    {
        key: 'listing_status',
        label: 'Trạng thái',
    },
    {
        key: 'status_reason',
        label: 'Lý do trạng thái',
    },
    {
        key: 'first_seen_at',
        label: 'Lần đầu ghi nhận',
    },
    {
        key: 'last_seen_at',
        label: 'Cập nhật gần nhất',
    },
    {
        key: 'state_hash',
        label: 'State hash',
    },
    {
        key: 'created_at',
        label: 'Ngày tạo DB',
    },
    {
        key: 'updated_at',
        label: 'Ngày cập nhật DB',
    },
];

const DEFAULT_FIELDS = [
    'external_listing_id',
    'listing_title',
    'listing_url',
    'seller',
    'category_name',
    'condition_name',
    'current_price',
    'shipping_price',
    'total_price',
    'currency',
    'listing_status',
    'last_seen_at',
];

export function ListingExportModal({
    open,
    marketplace,
    filters,
    onClose,
}: {
    open: boolean;
    marketplace: Marketplace;
    filters: ListingListParams;
    onClose: () => void;
}) {
    const [format, setFormat] =
        useState<ListingExportFormat>('xlsx');

    const [selectedFields, setSelectedFields] =
        useState<string[]>(DEFAULT_FIELDS);

    const [isExporting, setIsExporting] =
        useState(false);

    const [errorMessage, setErrorMessage] =
        useState('');

    useEffect(() => {
        if (!open) {
            return undefined;
        }

        const handleKeyDown = (
            event: KeyboardEvent,
        ) => {
            if (
                event.key === 'Escape' &&
                !isExporting
            ) {
                onClose();
            }
        };

        window.addEventListener(
            'keydown',
            handleKeyDown,
        );

        return () => {
            window.removeEventListener(
                'keydown',
                handleKeyDown,
            );
        };
    }, [open, isExporting, onClose]);

    const allSelected = useMemo(
        () =>
            selectedFields.length ===
            EXPORT_FIELDS.length,
        [selectedFields],
    );

    if (!open) {
        return null;
    }

    const toggleField = (field: string) => {
        setSelectedFields((current) => {
            if (current.includes(field)) {
                return current.filter(
                    (item) => item !== field,
                );
            }

            return [...current, field];
        });
    };

    const startDownload = (
        blob: Blob,
        filename: string,
    ) => {
        const objectUrl =
            URL.createObjectURL(blob);

        const anchor =
            document.createElement('a');

        anchor.href = objectUrl;
        anchor.download = filename;

        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();

        URL.revokeObjectURL(objectUrl);
    };

    const handleExport = async () => {
        if (selectedFields.length === 0) {
            setErrorMessage(
                'Vui lòng chọn ít nhất một trường.',
            );
            return;
        }

        setIsExporting(true);
        setErrorMessage('');

        try {
            // Chỉ sử dụng filter đã được Apply,
            // không dùng các giá trị form chưa áp dụng.
            const {
                page: _page,
                page_size: _pageSize,
                ...exportFilters
            } = filters;

            const result =
                await exportMarketplaceListings(
                    marketplace,
                    {
                        format,
                        fields: selectedFields,
                        filters: exportFilters,
                    },
                );

            if (result.kind === 'file') {
                startDownload(
                    result.blob,
                    result.filename,
                );

                onClose();
                return;
            }

            window.open(
                result.data.spreadsheet_url,
                '_blank',
                'noopener,noreferrer',
            );

            onClose();
        } catch (error) {
            console.error(error);

            setErrorMessage(
                'Không thể xuất dữ liệu. Vui lòng kiểm tra quyền hoặc thử lại.',
            );
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <div
            className="modal-backdrop"
            onMouseDown={(event) => {
                if (
                    event.target === event.currentTarget &&
                    !isExporting
                ) {
                    onClose();
                }
            }}
        >
            <section
                className="modal-panel modal-panel--export"
                role="dialog"
                aria-modal="true"
            >
                <header className="modal-header">
                    <div>
                        <h2 className="modal-title">
                            Xuất dữ liệu
                        </h2>

                        <p className="modal-subtitle">
                            Dữ liệu được xuất theo filter đang áp dụng
                        </p>
                    </div>

                    <button
                        type="button"
                        className="modal-close-button"
                        disabled={isExporting}
                        onClick={onClose}
                    >
                        ×
                    </button>
                </header>

                <div className="modal-body">
                    <label className="field-stack">
                        <span className="field-label">
                            Định dạng
                        </span>

                        <select
                            value={format}
                            onChange={(event) => {
                                setFormat(
                                    event.target
                                        .value as ListingExportFormat,
                                );
                            }}
                        >
                            <option value="xlsx">
                                Excel (.xlsx)
                            </option>

                            <option value="pdf">
                                PDF (.pdf)
                            </option>

                            <option value="google_sheets">
                                Google Sheets
                            </option>
                        </select>
                    </label>

                    {format === 'pdf' ? (
                        <p className="export-notice">
                            PDF hỗ trợ tối đa 10 trường và
                            5.000 dòng. Với dữ liệu lớn nên
                            chọn Excel hoặc Google Sheets.
                        </p>
                    ) : null}

                    <div className="export-fields-header">
                        <strong>Chọn trường dữ liệu</strong>

                        <button
                            type="button"
                            className="text-button"
                            onClick={() => {
                                setSelectedFields(
                                    allSelected
                                        ? []
                                        : EXPORT_FIELDS.map(
                                            (field) => field.key,
                                        ),
                                );
                            }}
                        >
                            {allSelected
                                ? 'Bỏ chọn tất cả'
                                : 'Chọn tất cả'}
                        </button>
                    </div>

                    <div className="export-field-grid">
                        {EXPORT_FIELDS.map((field) => (
                            <label
                                key={field.key}
                                className="export-field-option"
                            >
                                <input
                                    type="checkbox"
                                    checked={selectedFields.includes(
                                        field.key,
                                    )}
                                    onChange={() => {
                                        toggleField(field.key);
                                    }}
                                />

                                <span>{field.label}</span>
                            </label>
                        ))}
                    </div>

                    {errorMessage ? (
                        <div className="form-error">
                            {errorMessage}
                        </div>
                    ) : null}
                </div>

                <footer className="modal-footer">
                    <button
                        type="button"
                        className="action-button secondary"
                        disabled={isExporting}
                        onClick={onClose}
                    >
                        Hủy
                    </button>

                    <button
                        type="button"
                        className="action-button export-button"
                        disabled={
                            isExporting ||
                            selectedFields.length === 0
                        }
                        onClick={() => {
                            void handleExport();
                        }}
                    >
                        {isExporting
                            ? 'Đang xuất...'
                            : 'Xuất dữ liệu'}
                    </button>
                </footer>
            </section>
        </div>
    );
}