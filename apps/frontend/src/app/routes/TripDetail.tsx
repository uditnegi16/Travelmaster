import { useParams } from "react-router-dom";

export default function TripDetail() {
  const { id } = useParams();

  return (
    <div>
      <h1 className="text-2xl font-bold">Trip Details</h1>
      <p className="mt-4" style={{ color: "var(--text-muted)" }}>
        Trip ID: {id}
      </p>
    </div>
  );
}