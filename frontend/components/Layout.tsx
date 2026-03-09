import { useUser, UserButton, Protect } from "@clerk/nextjs";
import Link from "next/link";
import { useRouter } from "next/router";
import { ReactNode } from "react";
import PageTransition from "./PageTransition";

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user } = useUser();
  const router = useRouter();

  const isActive = (path: string) => router.pathname === path;

  return (
    <Protect fallback={
      <div className="min-h-screen flex items-center justify-center bg-[#0b0d17]">
        <div className="text-center">
          <p className="text-gray-400">Redirecting to sign in...</p>
        </div>
      </div>
    }>
      <div className="min-h-screen bg-[#0b0d17] bg-grid flex flex-col">
        {/* Navigation */}
        <nav className="bg-[#0f1121]/80 backdrop-blur-xl border-b border-white/10 sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center gap-8">
                <Link href="/dashboard" className="flex items-center">
                  <h1 className="text-xl font-bold text-white">
                    Stratos <span className="text-primary">AI</span>
                  </h1>
                </Link>

                <div className="hidden md:flex items-center gap-1">
                  {[
                    { href: "/dashboard", label: "Dashboard" },
                    { href: "/accounts", label: "Accounts" },
                    { href: "/advisor-team", label: "Advisor Team" },
                    { href: "/analysis", label: "Analysis" },
                  ].map(({ href, label }) => (
                    <Link
                      key={href}
                      href={href}
                      className={`text-sm font-medium px-3 py-1.5 rounded-md transition-all ${
                        isActive(href)
                          ? "text-primary bg-primary/10"
                          : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
                      }`}
                    >
                      {label}
                    </Link>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-4">
                <span className="hidden sm:inline text-sm text-gray-400">
                  {user?.firstName || user?.emailAddresses[0]?.emailAddress}
                </span>
                <UserButton afterSignOutUrl="/" />
              </div>
            </div>

            {/* Mobile Navigation */}
            <div className="md:hidden flex items-center gap-1 pb-3 overflow-x-auto">
              {[
                { href: "/dashboard", label: "Dashboard" },
                { href: "/accounts", label: "Accounts" },
                { href: "/advisor-team", label: "Advisor Team" },
                { href: "/analysis", label: "Analysis" },
              ].map(({ href, label }) => (
                <Link
                  key={href}
                  href={href}
                  className={`text-sm font-medium px-3 py-1.5 rounded-md transition-all whitespace-nowrap ${
                    isActive(href)
                      ? "text-primary bg-primary/10"
                      : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
                  }`}
                >
                  {label}
                </Link>
              ))}
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1">
          <PageTransition>
            {children}
          </PageTransition>
        </main>

        {/* Footer */}
        <footer className="bg-[#0f1121]/60 border-t border-white/5 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="bg-amber-500/5 border border-amber-500/10 rounded-lg p-4">
              <p className="text-sm text-amber-400/80 font-medium mb-2">
                Important Disclaimer
              </p>
              <p className="text-xs text-gray-500">
                This AI-generated advice has not been vetted by a qualified financial advisor and should not be used for trading decisions.
                For informational purposes only. Always consult with a licensed financial professional before making investment decisions.
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-white/5">
              <p className="text-xs text-gray-600 text-center">
                &copy; 2026 Stratos AI Financial Advisor. Powered by AI agents and built with care.
              </p>
            </div>
          </div>
        </footer>
      </div>
    </Protect>
  );
}
