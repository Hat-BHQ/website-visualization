import { NavLink } from 'react-router-dom';

import type {
    Marketplace,
} from '@/types/hqa';


export function MarketplaceTabs({
    marketplace,
}: {
    marketplace: Marketplace;
}) {
    const basePath =
        `/hqa/${marketplace}`;

    return (
        <nav className="marketplace-tabs">
            <NavLink
                end
                to={basePath}
                className={({ isActive }) =>
                    `marketplace-tab ${isActive ? 'active' : ''
                    }`
                }
            >
                Listings
            </NavLink>

            <NavLink
                to={`${basePath}/daily-report`}
                className={({ isActive }) =>
                    `marketplace-tab ${isActive ? 'active' : ''
                    }`
                }
            >
                Daily report
            </NavLink>
        </nav>
    );
}