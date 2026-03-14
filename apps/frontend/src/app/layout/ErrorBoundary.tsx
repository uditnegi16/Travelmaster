import { Component } from "react";
import type { ReactNode } from "react";

interface Props { children: ReactNode; }
interface State { hasError: boolean; error: string; }

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: "" };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error: error?.message || "Unknown error" };
  }

  componentDidCatch(error: Error, info: any) {
    console.error("ErrorBoundary caught:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6"
          style={{ background: "var(--bg-base)" }}>
          <div className="card p-8 max-w-md w-full text-center space-y-4">
            <div className="text-5xl">⚠️</div>
            <h2 className="font-display font-bold text-xl" style={{ color: "var(--text-primary)" }}>
              Something went wrong
            </h2>
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              {this.state.error}
            </p>
            <button className="btn btn-primary w-full"
              onClick={() => { this.setState({ hasError: false, error: "" }); window.location.href = "/app/dashboard"; }}>
              Back to Dashboard
            </button>
            <button className="btn w-full text-xs"
              onClick={() => this.setState({ hasError: false, error: "" })}>
              Try Again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}