import React from 'react';
import {
  LayoutDashboard,
  Map,
  ClipboardList,
  BookOpen,
  BarChart3,
  Brain,
  LogIn,
} from 'lucide-react';

export type ActiveTab =
  | 'console'
  | 'ward_map'
  | 'handover'
  | 'protocols'
  | 'proof'
  | 'how_it_thinks';

interface NavSidebarProps {
  activeTab: ActiveTab;
  onSelectTab: (tab: ActiveTab) => void;
  activeCardsCount: number;
}

export const NavSidebar: React.FC<NavSidebarProps> = ({
  activeTab,
  onSelectTab,
  activeCardsCount,
}) => {
  const navItems = [
    {
      id: 'console' as ActiveTab,
      label: 'Console',
      icon: LayoutDashboard,
      badge: activeCardsCount,
    },
    {
      id: 'ward_map' as ActiveTab,
      label: 'Ward map',
      icon: Map,
    },
    {
      id: 'handover' as ActiveTab,
      label: 'Handover',
      icon: ClipboardList,
    },
    {
      id: 'protocols' as ActiveTab,
      label: 'Protocols',
      icon: BookOpen,
    },
    {
      id: 'proof' as ActiveTab,
      label: 'Proof',
      icon: BarChart3,
    },
    {
      id: 'how_it_thinks' as ActiveTab,
      label: 'How it thinks',
      icon: Brain,
    },
  ];

  return (
    <aside className="w-20 bg-white border-r border-slate-200 flex flex-col justify-between items-center py-4 select-none shrink-0 z-20 shadow-xs">
      {/* Top Nav Items */}
      <div className="flex flex-col items-center gap-1 w-full">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`relative flex flex-col items-center justify-center w-16 py-2.5 rounded-xl transition-all ${
                isActive
                  ? 'bg-teal-50 text-teal-800 font-bold'
                  : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100/70 font-medium'
              }`}
              title={item.label}
            >
              {/* Optional Notification Badge */}
              {item.badge !== undefined && item.badge > 0 && (
                <span className="absolute top-1.5 right-2.5 w-4 h-4 bg-orange-500 text-white text-[10px] font-black rounded-full flex items-center justify-center shadow-xs">
                  {item.badge}
                </span>
              )}

              <Icon
                className={`w-5 h-5 mb-1 ${
                  isActive ? 'text-teal-700' : 'text-slate-500'
                }`}
              />
              <span className="text-[11px] leading-tight text-center tracking-tight">
                {item.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* Bottom Sign In */}
      <div className="w-full flex justify-center pt-2 border-t border-slate-100">
        <button
          onClick={() => alert('Ward staff authentication: Active session for Sr. Anjali (Staff Nurse 3B)')}
          className="flex flex-col items-center text-slate-400 hover:text-slate-700 py-1 transition"
          title="User Account"
        >
          <LogIn className="w-4 h-4 mb-0.5" />
          <span className="text-[10px] font-medium">Sign In</span>
        </button>
      </div>
    </aside>
  );
};
