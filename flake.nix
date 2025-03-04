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
          default = threedont;
          threedont = pkgs.python3.pkgs.buildPythonPackage {
            pname = "threedont";
            src = ./.;
            inherit version;
            pyproject = true;
            
            build-system = with pkgs.python3Packages; [
              scikit-build-core
            ];
            
            dontUseCmakeConfigure = true;

            nativeBuildInputs = with pkgs; [
              qt6.wrapQtAppsHook
              pkg-config
              cmake
              ninja
            ];
            
            dontWrapQtApps = true;
            # preFixup = ''
            #   makeWrapperArgs+=("''${qtWrapperArgs[@]}")
            # '';
            preFixup = ''
                wrapQtApp "$out/lib/python3.12/site-packages/threedont/viewer/viewer"
            '';
            
            buildInputs = with pkgs; [
              eigen
              tbb.dev
              qt6.qtbase
              libGL
            ] ++ lib.optionals stdenv.hostPlatform.isLinux [ qt6.qtwayland ];
            
            dependencies = with pkgs.python3Packages; [
              numpy
            ];
          };
        };

        apps = {
          default = {
            type = "app";
            program = let
              py = pkgs.python3.withPackages (_: [ self.packages.${system}.threedont ]);
            in
              "${py}/bin/python";
          };
        };

        devShells = {
          default = pkgs.mkShell {
            inputsFrom = [ self.packages.${system}.threedont ];
            packages = with pkgs; [
              python3Packages.build
              qt6.qttools
              gammaray
            ];
            nativeBuildInputs = with pkgs; [
              qt6.wrapQtAppsHook
              makeWrapper
            ];
            # https://discourse.nixos.org/t/python-qt-woes/11808/10
            shellHook = ''
              setQtEnvironment=$(mktemp --suffix .setQtEnvironment.sh)
              echo "shellHook: setQtEnvironment = $setQtEnvironment"
              makeWrapper "/bin/sh" "$setQtEnvironment" "''${qtWrapperArgs[@]}"
              sed "/^exec/d" -i "$setQtEnvironment"
              source "$setQtEnvironment"
            '';
          };
        };
      });
}
