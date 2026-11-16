import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertCircle, LoaderCircle, RefreshCw } from "lucide-react";

export function LoadingState({ label = "Loading intelligence data" }: { label?: string }) {
  return (
    <div className="panel flex min-h-40 items-center justify-center gap-3 p-6 text-sm text-slate-500">
      <LoaderCircle className="h-5 w-5 animate-spin text-accent" />
      {label}…
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="panel flex min-h-40 items-center justify-between gap-4 border-red-100 bg-red-50/60 p-6 text-sm text-red-700">
      <div className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
        <div>
          <p className="font-semibold">Data unavailable</p>
          <p className="mt-1 text-red-600/80">{message}</p>
        </div>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 rounded-lg border border-red-200 bg-white px-3 py-2 text-xs font-semibold text-red-700 transition hover:bg-red-50"
        >
          <RefreshCw className="h-3.5 w-3.5" /> Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex min-h-40 items-center justify-center rounded-xl border border-dashed border-line bg-slate-50/60 p-6 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}

interface PageErrorBoundaryProps {
  pageName: string;
  children: ReactNode;
}

interface PageErrorBoundaryState {
  hasError: boolean;
}

export class PageErrorBoundary extends Component<
  PageErrorBoundaryProps,
  PageErrorBoundaryState
> {
  state: PageErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): PageErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`Error rendering ${this.props.pageName}`, error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorState
          message={`${this.props.pageName} could not be rendered. Other dashboard sections remain available.`}
          onRetry={() => this.setState({ hasError: false })}
        />
      );
    }
    return this.props.children;
  }
}
