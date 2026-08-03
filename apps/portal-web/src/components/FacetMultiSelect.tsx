import {
    useEffect,
    useMemo,
    useRef,
    useState,
} from 'react';

import type {
    ListingFacetOption,
} from '@/types/hqa';

interface FacetMultiSelectProps {
    label: string;
    value: string[];
    options: ListingFacetOption[];
    searchable?: boolean;
    placeholder?: string;
    onApply: (values: string[]) => void;
}

export function FacetMultiSelect({
    label,
    value,
    options,
    searchable = true,
    placeholder = 'Tất cả',
    onApply,
}: FacetMultiSelectProps) {
    // Bọc toàn bộ dropdown để phát hiện click ra ngoài.
    const rootRef = useRef<HTMLDivElement | null>(null);

    // Trạng thái đóng/mở giờ do React quản lý (controlled),
    // thay cho thuộc tính open mặc định của thẻ <details>.
    const [open, setOpen] = useState(false);

    const [draft, setDraft] =
        useState<string[]>(value);

    const [search, setSearch] =
        useState('');

    useEffect(() => {
        setDraft(value);
    }, [value]);

    // Đóng menu khi click ra ngoài (bao gồm click sang select khác)
    // hoặc khi nhấn Escape. Chỉ gắn listener khi menu đang mở.
    useEffect(() => {
        if (!open) {
            return;
        }

        const closeAndReset = () => {
            setDraft(value);
            setSearch('');
            setOpen(false);
        };

        const handlePointerDown = (event: PointerEvent) => {
            if (
                rootRef.current &&
                !rootRef.current.contains(
                    event.target as Node,
                )
            ) {
                closeAndReset();
            }
        };

        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                closeAndReset();
            }
        };

        document.addEventListener(
            'pointerdown',
            handlePointerDown,
        );

        document.addEventListener(
            'keydown',
            handleKeyDown,
        );

        return () => {
            document.removeEventListener(
                'pointerdown',
                handlePointerDown,
            );

            document.removeEventListener(
                'keydown',
                handleKeyDown,
            );
        };
    }, [open, value]);

    const filteredOptions = useMemo(() => {
        const keyword = search.trim().toLowerCase();

        if (!keyword) {
            return options;
        }

        return options.filter((option) =>
            option.label.toLowerCase().includes(keyword),
        );
    }, [options, search]);

    const selectedText =
        value.length === 0
            ? placeholder
            : value.length === 1
                ? (
                    options.find(
                        (option) => option.value === value[0],
                    )?.label ?? value[0]
                )
                : `${value.length} giá trị`;

    const toggleValue = (optionValue: string) => {
        setDraft((current) =>
            current.includes(optionValue)
                ? current.filter(
                    (item) => item !== optionValue,
                )
                : [...current, optionValue],
        );
    };

    const handleCancel = () => {
        setDraft(value);
        setSearch('');
        setOpen(false);
    };

    const handleApply = () => {
        onApply(draft);
        setSearch('');
        setOpen(false);
    };

    const selectVisible = () => {
        const visibleValues =
            filteredOptions.map(
                (option) => option.value,
            );

        setDraft((current) => [
            ...new Set([
                ...current,
                ...visibleValues,
            ]),
        ]);
    };

    return (
        <div
            className="field-stack"
            ref={rootRef}
        >
            <span className="field-label">
                {label}
            </span>

            <div className="facet-select">
                <button
                    type="button"
                    className="facet-select__summary"
                    aria-haspopup="listbox"
                    aria-expanded={open}
                    onClick={() =>
                        setOpen((current) => !current)
                    }
                >
                    <span>{selectedText}</span>
                    <span>▾</span>
                </button>

                {open ? (
                    <div className="facet-select__menu">
                        <div className="facet-select__actions">
                            <button
                                type="button"
                                onClick={selectVisible}
                            >
                                Chọn tất cả
                            </button>

                            <button
                                type="button"
                                onClick={() => setDraft([])}
                            >
                                Xóa
                            </button>
                        </div>

                        {searchable ? (
                            <input
                                type="search"
                                value={search}
                                onChange={(event) =>
                                    setSearch(event.target.value)
                                }
                                placeholder="Tìm kiếm..."
                            />
                        ) : null}

                        <div className="facet-select__options">
                            {filteredOptions.map((option) => (
                                <label
                                    key={option.value}
                                    className="facet-select__option"
                                >
                                    <input
                                        type="checkbox"
                                        checked={draft.includes(
                                            option.value,
                                        )}
                                        onChange={() =>
                                            toggleValue(option.value)
                                        }
                                    />

                                    <span className="facet-select__label">
                                        {option.label}
                                    </span>

                                    <span className="facet-select__count">
                                        {option.count.toLocaleString(
                                            'vi-VN',
                                        )}
                                    </span>
                                </label>
                            ))}

                            {filteredOptions.length === 0 ? (
                                <div className="facet-select__empty">
                                    Không tìm thấy giá trị
                                </div>
                            ) : null}
                        </div>

                        <div className="facet-select__footer">
                            <button
                                type="button"
                                onClick={handleCancel}
                            >
                                Hủy
                            </button>

                            <button
                                className="facet-select__ok"
                                type="button"
                                onClick={handleApply}
                            >
                                OK
                            </button>
                        </div>
                    </div>
                ) : null}
            </div>
        </div>
    );
}
