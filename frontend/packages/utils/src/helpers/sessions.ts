import { Session } from "@vbkg/types";
import { SESSION_STORAGE_KEY } from "../constants";
import { jwtDecode } from "jwt-decode";

export const setSession = (session: Session | null) => {
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
};

export const getSession = (): Session | null => {
  const session = localStorage.getItem(SESSION_STORAGE_KEY);
  return session ? JSON.parse(session) : null;
};

export const isValidSession = (session: Session | null): boolean => {
  if (!session) return false;
  if (!session.session || !session.user) return false;
  if (!session.session.accessToken || !session.session.refreshToken)
    return false;
  if (!session.user.id || !session.user.name || !session.user.email)
    return false;

  const token = session?.session.accessToken;
  const decodedToken = jwtDecode(token);
  const exp = Number(decodedToken?.exp) * 1000;
  if (Date.now() > exp) {
    return false; // Token expired
  }

  return true;
};
