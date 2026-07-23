import { postRequest } from "./api";


// ================= REGISTER =================
export const registerUser = async (data) => {
  try {
    const response = await postRequest("/auth/register", data);

    return {
      success: true,
      message: response.message || "Registration successful",
      user: response.user,
    };

  } catch (error) {
    throw new Error(error.message || "Registration failed");
  }
};


// ================= FRONTEND LOG =================
export const sendFrontendLog = async (data) => {
  try {

    const response = await postRequest(
      "/frontend-log",
      data
    );

    return response;

  } catch(error){

    console.log("Frontend log failed:", error.message);

  }
};


// ================= LOGIN =================
export const loginUser = async ({ email, password }) => {
  try {
    const response = await postRequest("/auth/login", {
      email,
      password,
    });

    return {
      success: true,
      message: response.message || "Login successful",
      user: response.user,
      token: response.token,
    };

  } catch (error) {
    throw new Error(error.message || "Invalid credentials");
  }
};