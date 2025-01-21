# nix comment
{
  description = "3dont, ontology pointcloud visualizer";

  inputs.nixpkgs.url = "nixpkgs/nixos-24.11";

  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    let
      version = "0.0.1";
      overlay = final: prev: { };
    in

    flake-utils.lib.eachDefaultSystem (system:
      let pkgs = (nixpkgs.legacyPackages.${system}.extend overlay); in
      {

        packages = rec {
          default = visualizer;
          visualizer = pkgs.python3.pkgs.toPythonModule ( pkgs.stdenv.mkDerivation {
            pname = "3D-ont";
            src = ./.;
            inherit version;

            nativeBuildInputs = with pkgs; [
              libsForQt5.qt5.wrapQtAppsHook
              cmake
              pkg-config
            ];
            
            buildInputs = with pkgs; [
              eigen
              python3
              tbb.dev
              libsForQt5.qt5.qtbase
              libGL
              python3Packages.numpy
            ];
            
            propagatebBuildInputs = with pkgs.python3Packages; [
              numpy
            ];
            
            cmakeFlags = [
              "-DTBB_ROOT=${pkgs.tbb.out}"
              "-DTBB_INCLUDE_DIR=${pkgs.tbb.dev}/include"
            ];
          });
        };

        apps = {
          default = {
            type = "app";
            program = "${self.defaultPackage.${system}}/bin/a.out";
          };
        };

        devShells = {
          default = pkgs.mkShell {
            inputsFrom = [ self.packages.${system}.visualizer ];
          };
        };
      });
}
