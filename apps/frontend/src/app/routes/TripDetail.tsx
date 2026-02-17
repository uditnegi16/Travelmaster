import { Routes, useParams } from "react-router-dom";
import AppShell from "../layout/AppShell";

export default function TripDetail() {
  const { id } = useParams();

  return (
      <><div>
      <h1 className="text-2xl font-bold">Trip Details</h1>
      <p className="mt-4 text-slate-400">
        Trip ID: {id}
      </p>
    </div><Routes>
        <Route path="/app/session/:id" element={<TripDetail />} />
      </Routes></>
  );
}
