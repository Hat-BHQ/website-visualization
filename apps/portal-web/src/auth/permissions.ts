import type { CurrentUser } from '@/types/auth';
import type { Marketplace } from '@/types/hqa';

/**
 * Kiểm tra user có quyền export marketplace hay không.
 *
 * Điều kiện nghiệp vụ:
 * - Superadmin: luôn được export.
 * - HQA Admin: phải có đúng permission export.
 * - HQA User: không được export.
 */
export function canExportHqaMarketplace(
    user: CurrentUser,
    marketplace: Marketplace,
) {
    if (user.is_superadmin) {
        return true;
    }

    const hqaModule = user.modules.find(
        (module) =>
            module.code.toUpperCase() === 'HQA',
    );

    if (!hqaModule) {
        return false;
    }

    const requiredPermission =
        `hqa.${marketplace}.export`;

    // Permission là nguồn sự thật duy nhất. Role đã được backend
    // ánh xạ thành danh sách permission trong /api/auth/me.
    return hqaModule.permissions.includes(
        requiredPermission,
    );
}