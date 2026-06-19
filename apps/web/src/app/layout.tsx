import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as SonnerToaster } from "@/components/ui/sonner";
import { ThemeProvider } from "@/components/theme/ThemeProvider";

export const metadata: Metadata = {
  title: "山海教育 · AI幼教ProMax可视化工作台",
  description:
    "山海教育 AI 教学资源生产指挥台 —— 从教材资料到教案、导入视频、PPT 与最终交付的全流程可视化工作台。",
  applicationName: "山海教育 ProMax 工作台",
  authors: [{ name: "山海教育" }],
  keywords: ["山海教育", "AI幼教", "ProMax", "教学资源", "工作台"],
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
  formatDetection: { telephone: false },
  openGraph: {
    title: "山海教育 · AI幼教ProMax可视化工作台",
    description: "AI 教学资源生产指挥台",
    siteName: "山海教育",
    type: "website",
    locale: "zh_CN",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: "#2d4356",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="antialiased bg-background text-foreground min-h-screen">
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <Toaster />
          <SonnerToaster position="top-center" richColors={false} />
        </ThemeProvider>
      </body>
    </html>
  );
}
