import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error boundary caught:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = '/dashboard';
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#0b0d17] flex items-center justify-center px-4">
          <div className="text-center max-w-md">
            <h1 className="text-4xl font-bold text-red-400 mb-4">Something went wrong</h1>
            <p className="text-gray-400 mb-6">
              An unexpected error occurred. The error has been logged and we&apos;ll look into it.
            </p>
            {this.state.error && (
              <details className="mb-6 text-left bg-white/5 border border-white/10 p-4 rounded-lg">
                <summary className="cursor-pointer font-medium text-gray-300">Error details</summary>
                <pre className="mt-2 text-xs overflow-auto text-gray-500">{this.state.error.toString()}</pre>
              </details>
            )}
            <button
              onClick={this.handleReset}
              className="bg-primary/80 hover:bg-primary text-white px-6 py-3 rounded-lg transition-colors"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
