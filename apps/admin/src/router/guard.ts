// Auth navigation wiring with injected dependencies (no store import → no cycles).
import type {
  RouteLocationNormalized,
  RouteLocationRaw,
  Router,
} from "vue-router";
import { redirectQuery, resolveTarget, takeLoginHandoff } from "./redirect";

export interface AuthState {
  signedIn: boolean;
  mustChangePassword: boolean;
}

function carriedTarget(to: RouteLocationNormalized): unknown {
  return to.path === "/login" || to.path === "/change-password"
    ? to.query.redirect
    : to.fullPath;
}

export function authGuard(
  to: RouteLocationNormalized,
  auth: AuthState,
): RouteLocationRaw | undefined {
  if (!auth.signedIn) {
    if (to.path === "/login") return undefined;
    return { path: "/login", query: redirectQuery(carriedTarget(to)) };
  }
  if (auth.mustChangePassword) {
    if (to.path === "/change-password") return undefined;
    return {
      path: "/change-password",
      query: redirectQuery(carriedTarget(to)),
    };
  }
  if (to.path === "/login" || to.path === "/change-password")
    return resolveTarget(to.query.redirect);
  return undefined;
}

export function installAuthNavigation(
  router: Router,
  deps: {
    auth: () => AuthState;
    requirePassword: () => void;
    events: Pick<EventTarget, "addEventListener">;
  },
) {
  router.beforeEach((to) => authGuard(to, deps.auth()));
  deps.events.addEventListener("admin-session-ended", () => {
    // Explicit logout/expiry → bare /login; password change hand-off keeps target.
    const target = takeLoginHandoff();
    void router.replace({ path: "/login", query: redirectQuery(target) });
  });
  deps.events.addEventListener("admin-password-required", () => {
    deps.requirePassword();
    const current = router.currentRoute.value;
    if (current.path === "/change-password") return;
    void router.replace({
      path: "/change-password",
      query: redirectQuery(carriedTarget(current)),
    });
  });
}
