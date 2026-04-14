import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import StitchingPipeline from "../components/StitchingPipeline";

export const metadata = {
  title: "Pipeline | Pano",
  description:
    "Run the full panorama stitching pipeline — Harris, SIFT, RANSAC, Homography & Warping — and visualize every step.",
};

export default function PipelinePage() {
  return (
    <main className="flex flex-col min-h-screen">
      <Navbar />
      <section className="flex-1 pt-4 pb-12">
        <StitchingPipeline />
      </section>
      <Footer />
    </main>
  );
}
