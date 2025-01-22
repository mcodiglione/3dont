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
            pname = "3D-ont";
            src = ./.;
            inherit version;
            pyproject = true;
            
            build-system = with pkgs.python3Packages; [
              scikit-build-core
            ];
            
            dontUseCmakeConfigure = true;

            nativeBuildInputs = with pkgs; [
              libsForQt5.qt5.wrapQtAppsHook
              pkg-config
              cmake
              ninja
            ];
            
            dontWrapQtApps = true;
            # preFixup = ''
            #   makeWrapperArgs+=("''${qtWrapperArgs[@]}")
            # '';
            preFixup = ''
                wrapQtApp "$out/lib/python3.12/site-packages/bin/viewer"
            '';
            
            buildInputs = with pkgs; [
              eigen
              tbb.dev
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
            packages = with pkgs.python3Packages; [
              build
            ];
            LD_LIBRARY_PATH="/run/opengl-driver/lib:/run/opengl-driver-32/lib";
            QT_SCALE_FACTOR="0.5";
          };
        };
      });
}
