export type Session = {
  session: {
    accessToken: string;
    refreshToken: string;
  };
  user: {
    id: string;
    name: string;
    email: string;
    roles: string[];
  };
};
