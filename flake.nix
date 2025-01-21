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
          visualizer = pkgs.python3.pkgs.buildPythonPackage {
            pname = "3dont";
            src = ./.;
            inherit version;

            nativeBuildInputs = with pkgs; [
              libsForQt5.qt5.wrapQtAppsHook
            ];
            
            buildInputs = with pkgs; [
              eigen
              python3
              tbb
              libsForQt5.qt5.qtbase
              libGL
            ];
            
            dependencies = with pkgs.python3Packages; [
              numpy
            ];
          };
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
