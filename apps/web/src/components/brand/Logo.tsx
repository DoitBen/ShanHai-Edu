import { cn } from "@/lib/utils";

type LogoMarkProps = {
  size?: number;
  className?: string;
  withBg?: boolean;
};

/**
 * 山海教育 品牌标记
 * 山峰（深青灰底上的米白三角）+ 海浪（古铜金）+ 指引星
 * 完全本地 inline SVG，无任何外部依赖。
 */
export function LogoMark({ size = 40, className, withBg = true }: LogoMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("shrink-0", className)}
      role="img"
      aria-label="山海教育"
    >
      {withBg && (
        <rect width="64" height="64" rx="14" fill="var(--brand-primary, #2D4356)" />
      )}
      {/* 山峰 */}
      <path
        d="M12 43 L25 22 L33 35 L42 19 L52 43 Z"
        fill={withBg ? "#F4EFE6" : "currentColor"}
        fillOpacity={withBg ? 0.95 : 1}
      />
      {/* 海浪 / 翻开的书页 */}
      <path
        d="M12 45 Q21 39 32 45 Q43 51 52 45 L52 52 Q43 58 32 52 Q21 46 12 52 Z"
        fill="#9C7C4E"
        fillOpacity={0.9}
      />
      {/* 指引星 */}
      <circle cx="45" cy="17" r="2.3" fill="#C9A36A" />
    </svg>
  );
}

type LogoProps = {
  size?: number;
  showWordmark?: boolean;
  subline?: string;
  className?: string;
  wordmarkClassName?: string;
};

/**
 * 完整品牌锁形：标记 + “山海教育”字标
 */
export function Logo({
  size = 36,
  showWordmark = true,
  subline,
  className,
  wordmarkClassName,
}: LogoProps) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <LogoMark size={size} />
      {showWordmark && (
        <div className="flex flex-col leading-none">
          <span
            className={cn(
              "font-semibold tracking-[0.18em] text-[1.05rem]",
              wordmarkClassName
            )}
          >
            山海教育
          </span>
          {subline && (
            <span className="mt-1 text-[0.7rem] tracking-[0.22em] text-muted-foreground">
              {subline}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export function LogoWordmark({ className }: { className?: string }) {
  return (
    <span className={cn("font-semibold tracking-[0.18em]", className)}>
      山海教育
    </span>
  );
}
