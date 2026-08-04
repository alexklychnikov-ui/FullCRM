export type UserProfile = {
  id: string;
  email: string;
  fullName: string;
  isActive: boolean;
};

export type OrganizationProfile = {
  id: string;
  name: string;
  slug: string;
};

export type AuthProfile = {
  user: UserProfile;
  organization: OrganizationProfile;
  roles: string[];
  permissions: string[];
  modules: string[];
};

export type LoginPayload = {
  email: string;
  password: string;
};
