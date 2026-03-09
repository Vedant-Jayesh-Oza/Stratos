import { SignInButton, SignUpButton, SignedIn, SignedOut, UserButton } from "@clerk/nextjs";
import Link from "next/link";
import Head from "next/head";
import { Crosshair, BarChart3, TrendingUp, Target, Zap, Shield } from "lucide-react";

export default function Home() {
  return (
    <>
      <Head>
        <title>Stratos AI Financial Advisor - Intelligent Portfolio Management</title>
      </Head>
    <div className="min-h-screen bg-[#0b0d17] bg-grid">
      {/* Navigation */}
      <nav className="px-8 py-5 bg-[#0f1121]/80 backdrop-blur-xl border-b border-white/10 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="text-2xl font-bold text-white">
            Stratos <span className="text-primary">AI</span>
          </div>
          <div className="flex gap-3">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="px-5 py-2 text-gray-300 border border-white/10 rounded-lg hover:bg-white/5 transition-all text-sm">
                  Sign In
                </button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button className="px-5 py-2 bg-primary/80 text-white rounded-lg hover:bg-primary transition-all text-sm">
                  Get Started
                </button>
              </SignUpButton>
            </SignedOut>
            <SignedIn>
              <div className="flex items-center gap-4">
                <Link href="/dashboard">
                  <button className="px-5 py-2 bg-ai-accent/80 text-white rounded-lg hover:bg-ai-accent transition-all text-sm">
                    Go to Dashboard
                  </button>
                </Link>
                <UserButton afterSignOutUrl="/" />
              </div>
            </SignedIn>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="px-8 py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent pointer-events-none" />
        <div className="max-w-7xl mx-auto text-center relative">
          <div className="inline-block mb-6 px-4 py-1.5 rounded-full border border-white/10 bg-white/5 text-xs text-gray-400">
            Powered by Multi-Agent AI
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
            Your AI-Powered{" "}
            <span className="bg-gradient-to-r from-primary to-ai-accent bg-clip-text text-transparent">
              Financial Future
            </span>
          </h1>
          <p className="text-lg text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed">
            Experience the power of autonomous AI agents working together to analyze your portfolio,
            plan your retirement, and optimize your investments.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <SignedOut>
              <SignUpButton mode="modal">
                <button className="px-8 py-3.5 bg-ai-accent/80 text-white rounded-lg hover:bg-ai-accent transition-all shadow-lg shadow-ai-accent/20 hover:shadow-ai-accent/30 font-medium">
                  Start Your Analysis
                </button>
              </SignUpButton>
            </SignedOut>
            <SignedIn>
              <Link href="/dashboard">
                <button className="px-8 py-3.5 bg-ai-accent/80 text-white rounded-lg hover:bg-ai-accent transition-all shadow-lg shadow-ai-accent/20 hover:shadow-ai-accent/30 font-medium">
                  Open Dashboard
                </button>
              </Link>
            </SignedIn>
            <button className="px-8 py-3.5 border border-white/10 text-gray-300 rounded-lg hover:bg-white/5 transition-all font-medium">
              Watch Demo
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-8 py-20">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-white mb-4">
            Meet Your AI Advisory Team
          </h2>
          <p className="text-gray-500 text-center mb-12 max-w-xl mx-auto">
            Four specialized agents collaborating in real-time to deliver comprehensive financial insights.
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { Icon: Crosshair, name: "Financial Planner", desc: "Coordinates your complete financial analysis with intelligent orchestration", color: "text-ai-accent", glow: "shadow-ai-accent/20" },
              { Icon: BarChart3, name: "Portfolio Analyst", desc: "Deep analysis of holdings, performance metrics, and risk assessment", color: "text-primary", glow: "shadow-primary/20" },
              { Icon: TrendingUp, name: "Chart Specialist", desc: "Visualizes your portfolio composition with interactive charts", color: "text-success", glow: "shadow-success/20" },
              { Icon: Target, name: "Retirement Planner", desc: "Projects your retirement readiness with Monte Carlo simulations", color: "text-accent", glow: "shadow-accent/20" },
            ].map(({ Icon, name, desc, color, glow }) => (
              <div key={name} className={`glass-card p-6 text-center hover:bg-white/[0.06] transition-all hover:shadow-lg ${glow}`}>
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-lg bg-white/5 mb-4 ${color}`}>
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className={`text-lg font-semibold mb-2 ${color}`}>{name}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="px-8 py-20">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-white mb-12">
            Enterprise-Grade AI Advisory
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { Icon: Zap, title: "Real-Time Analysis", desc: "Watch AI agents collaborate in parallel to analyze your complete financial picture", color: "text-accent" },
              { Icon: Shield, title: "Bank-Level Security", desc: "Your data is protected with enterprise security and row-level access controls", color: "text-primary" },
              { Icon: BarChart3, title: "Comprehensive Reports", desc: "Detailed markdown reports with interactive charts and retirement projections", color: "text-ai-accent" },
            ].map(({ Icon, title, desc, color }) => (
              <div key={title} className="glass-card p-8">
                <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg bg-white/5 mb-4 ${color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-3">{title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-8 py-20">
        <div className="max-w-4xl mx-auto">
          <div className="glass-card-strong p-12 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-ai-accent/10 via-transparent to-primary/10 pointer-events-none" />
            <div className="relative">
              <h2 className="text-3xl font-bold text-white mb-4">
                Ready to Transform Your Financial Future?
              </h2>
              <p className="text-lg text-gray-400 mb-8">
                Join thousands of investors using AI to optimize their portfolios
              </p>
              <SignUpButton mode="modal">
                <button className="px-8 py-3.5 bg-accent/90 text-black font-semibold rounded-lg hover:bg-accent transition-all shadow-lg shadow-accent/20">
                  Get Started Free
                </button>
              </SignUpButton>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-8 py-6 border-t border-white/5 text-center">
        <p className="text-gray-600 text-xs">&copy; 2026 Stratos AI Financial Advisor. All rights reserved.</p>
        <p className="mt-2 text-gray-700 text-xs">
          This AI-generated advice has not been vetted by a qualified financial advisor and should not be used for trading decisions.
          For informational purposes only.
        </p>
      </footer>
    </div>
    </>
  );
}
