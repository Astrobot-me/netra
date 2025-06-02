// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { addDoc, collection, getDocs, getFirestore, limit, orderBy, query } from "firebase/firestore";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: import.meta.env.VITE_APIKEY,
  authDomain: import.meta.env.VITE_AUTHDOMAIN,
  projectId: import.meta.env.VITE_PROJECTID,
  storageBucket: import.meta.env.VITE_STORAGEBUCKET,
  messagingSenderId: import.meta.env.VITE_MESSAGINGSENDERID,
  appId: import.meta.env.VITE_APPID,
  measurementId: "G-QH22HW4L1Q"
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);


export const fetchLatestSession = async () => {
  try {
    const q = query(
      collection(db, 'traffic_sessions'),
      orderBy('start_time', 'desc'), // most recent first
      limit(1) // only get the top one
    );

    const querySnapshot = await getDocs(q);

    if (!querySnapshot.empty) {
      const doc = querySnapshot.docs[0];
      return { id: doc.id, ...doc.data() }; // return the document with its ID
    } else {
      console.warn('No sessions found in traffic_sessions.');
      return null;
    }
  } catch (error) {
    console.error('Error fetching latest session:', error);
    return null;
  }
};

export const addDocument = async (collectionName: string, data : any) => {
  try {
    const docRef = await addDoc(collection(db, collectionName), data);
    console.log("Document written with ID:", docRef.id);
    return docRef;
  } catch (error) {
    console.error("Error adding document:", error);
    throw error;
  }
};
