import { useUserMe } from "@vbkg/api-client";
import { USER_ROLES } from "@vbkg/utils";
import { useMemo } from "react";

export const usePermissionUtils = () => {
  const { data: currentUser } = useUserMe();

  const hasPermission = useMemo(() => {
    return (permission: string): boolean => {
      if (!currentUser?.data?.permissions) return false;
      return currentUser.data.permissions?.includes(permission);
    };
  }, [currentUser?.data?.permissions]);

  const hasRole = useMemo(() => {
    return (role: string): boolean => {
      if (!currentUser?.data?.roles) return false;
      return currentUser.data.roles.includes(role);
    };
  }, [currentUser?.data?.roles]);

  const hasAnyRole = useMemo(() => {
    return (roles: string[]): boolean => {
      if (!currentUser?.data?.roles) return false;
      return roles.some((role) => currentUser.data.roles.includes(role));
    };
  }, [currentUser?.data?.roles]);

  const hasAnyPermission = useMemo(() => {
    return (permissions: string[]): boolean => {
      if (!currentUser?.data?.permissions) return false;
      return permissions.some((permission) =>
        currentUser.data.permissions.includes(permission),
      );
    };
  }, [currentUser?.data?.permissions]);

  const isAdmin = useMemo(() => {
    return hasRole(USER_ROLES.ADMIN);
  }, [hasRole]);

  const isExpert = useMemo(() => {
    return hasRole(USER_ROLES.EXPERT);
  }, [hasRole]);

  return {
    currentUser: currentUser?.data,
    hasPermission,
    hasRole,
    hasAnyRole,
    hasAnyPermission,
    isAdmin,
    isExpert,
    permissions: currentUser?.data?.permissions || [],
    roles: currentUser?.data?.roles || [],
  };
};
