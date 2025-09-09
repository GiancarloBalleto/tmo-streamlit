import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyCPQ-CKs6Ciuefl4XytOwgrmsEfTLd36UM",
  authDomain: "cobranzaiq-94010.firebaseapp.com",
  projectId: "cobranzaiq-94010",
  storageBucket: "cobranzaiq-94010.firebasestorage.app",
  messagingSenderId: "174685540848",
  appId: "1:174685540848:web:e06ee08f23e33076b80d35",
};

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
