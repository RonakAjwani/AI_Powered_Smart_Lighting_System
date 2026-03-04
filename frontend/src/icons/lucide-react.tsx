'use client';

import * as React from 'react';

export type IconProps = React.SVGProps<SVGSVGElement> & { size?: number | string };

function makeIcon(path: React.ReactNode) {
  return function Icon({ size = 24, stroke = 'currentColor', strokeWidth = 2, fill = 'none', className, ...rest }: IconProps) {
    return (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill={fill}
        stroke={stroke}
        strokeWidth={strokeWidth as number}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
        {...rest}
      >
        {path}
      </svg>
    );
  };
}

export const Activity = makeIcon(<path d="M22 12h-2.5a2 2 0 0 0-1.9 1.5l-2.4 8.3L9.2 2.2 6.8 10.5A2 2 0 0 1 4.5 12H2" />);
export const CloudSun = makeIcon(<><path d="M12 2v3" /><path d="M5.22 5.22 7.34 7.34" /><path d="M2 12h3" /><path d="M5.22 18.78 7.34 16.66" /><path d="M12 19v3" /><path d="M18.78 18.78 16.66 16.66" /><path d="M21 12h-3" /><path d="M18.78 5.22 16.66 7.34" /><path d="M7 16a4 4 0 1 1 6-5.33A5 5 0 1 1 7 16Z" /></>);
export const ShieldAlert = makeIcon(<><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" /><path d="M12 8v4" /><path d="M12 16h.01" /></>);
export const Zap = makeIcon(<path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z" />);
export const CloudRain = makeIcon(<><path d="M4 14a4 4 0 1 1 2.9-6.8A6 6 0 1 1 20 11" /><path d="M16 14v6" /><path d="M8 14v6" /><path d="M12 16v6" /></>);
export const CloudFog = makeIcon(<><path d="M3 15h13a4 4 0 1 0-3.6-6A6 6 0 1 0 3 12" /><path d="M3 21h18M3 17h12" /></>);
export const Wind = makeIcon(<><path d="M3 12h15a3 3 0 1 0-3-3" /><path d="M4 18h9a2 2 0 1 0-2-2" /></>);
export const Sun = makeIcon(<><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34 19.07 4.93" /></>);
export const Target = makeIcon(<><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="4" /><path d="M22 12h-2M4 12H2M12 2v2M12 22v-2" /></>);
export const Lightbulb = makeIcon(<><path d="M9 18h6" /><path d="M10 22h4" /><path d="M2 12a10 10 0 1 1 20 0c0 3.1-1.6 5-3 6-1 1-1 2-1 2H6s0-1-1-2c-1.4-1-3-2.9-3-6Z" /></>);
export const AlertTriangle = makeIcon(<><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" /><path d="M12 9v4" /><path d="M12 17h.01" /></>);
export const Settings = makeIcon(<><path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V22a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H2a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06A2 2 0 1 1 4.1 4.1l.06.06a1.65 1.65 0 0 0 1.82.33H6a1.65 1.65 0 0 0 1-1.51V2a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0 .33 1.82V8" /></>);
export const FileText = makeIcon(<><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" /><path d="M14 2v6h6" /><path d="M16 13H8" /><path d="M16 17H8" /><path d="M10 9H8" /></>);
export const ShieldCheck = makeIcon(<><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" /><path d="m9 12 2 2 4-4" /></>);
export const Globe = makeIcon(<><circle cx="12" cy="12" r="10" /><path d="M2 12h20" /><path d="M12 2a15.3 15.3 0 0 1 0 20" /><path d="M12 2a15.3 15.3 0 0 0 0 20" /></>);
export const Bell = makeIcon(<><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a2 2 0 0 0 3.4 0" /></>);
export const CheckCircle = makeIcon(<><path d="M22 11.1V12a10 10 0 1 1-5.93-9.14" /><path d="m9 11 3 3L22 4" /></>);
export const Database = makeIcon(<><ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 5v6c0 1.7-4 3-9 3s-9-1.3-9-3V5" /><path d="M3 11v6c0 1.7 4 3 9 3s9-1.3 9-3v-6" /></>);
export const Battery = makeIcon(<><rect x="1" y="6" width="18" height="12" rx="2" /><path d="M23 13v-4" /></>);
export const Wifi = makeIcon(<><path d="M5 12.55a11 11 0 0 1 14 0" /><path d="M8.5 16a7 7 0 0 1 7 0" /><path d="M12 20h.01" /></>);
export const Radio = makeIcon(<circle cx="12" cy="12" r="2" />);

// Default export compatibility (not used in our codebase)
const index = {} as const;
export { index };

export default index;

