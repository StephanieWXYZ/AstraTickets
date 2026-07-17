import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { getCurrentUser, login, register } from "../api/client";
import type { RegisterInput, User } from "../types";

const TOKEN_KEY = "astratickets_access_token";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<User>;
  signUp: (input: RegisterInput) => Promise<User>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() =>
    sessionStorage.getItem(TOKEN_KEY),
  );
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(token));

  const clearSession = useCallback(() => {
    sessionStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    let active = true;
    getCurrentUser(token)
      .then((currentUser) => {
        if (active) setUser(currentUser);
      })
      .catch(() => {
        if (active) clearSession();
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [clearSession, token]);

  const signIn = useCallback(async (email: string, password: string) => {
    const tokenResponse = await login(email, password);
    const currentUser = await getCurrentUser(tokenResponse.access_token);
    sessionStorage.setItem(TOKEN_KEY, tokenResponse.access_token);
    setToken(tokenResponse.access_token);
    setUser(currentUser);
    return currentUser;
  }, []);

  const signUp = useCallback(
    async (input: RegisterInput) => {
      await register(input);
      return signIn(input.email, input.password);
    },
    [signIn],
  );

  const value = useMemo(
    () => ({ user, token, isLoading, signIn, signUp, signOut: clearSession }),
    [clearSession, isLoading, signIn, signUp, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
