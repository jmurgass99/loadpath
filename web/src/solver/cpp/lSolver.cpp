// lSolver.cpp — C++ WebAssembly kernel for Loadpath 2D/3D frame stiffness and
// Monforton-Wu (1963) semi-rigid connection fixity factor evaluation.

extern "C" {

// Computes Monforton-Wu rotational fixity factor:
//   gamma = 1 / (1 + 3 * E * I / (Sj * L))
double monfortonFixityFactor(double Sj, double E, double I, double L) {
    return 1.0 / (1.0 + (3.0 * E * I) / (Sj * L));
}

// Computes Euler-Bernoulli shear stiffness 12 * E * I / L^3
double beamFlexuralStiffness(double E, double I, double L) {
    return (12.0 * E * I) / (L * L * L);
}

}
