# nix comment
{
  description = "3dont, ontology pointcloud visualizer";

  inputs.nixpkgs.url = "nixpkgs/nixos-25.05";

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
          threedont = pkgs.python3.pkgs.buildPythonApplication {
            pname = "threedont";
            src = ./.;
            inherit version;
            pyproject = true;

            stdenv = pkgs.clangStdenv; # better interoperability with darwin build env

#            cmakeFlags = [
#              "-DCMAKE_BUILD_TYPE=Debug"
#            ];
            
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

            # Fix problem caused by https://github.com/NixOS/nixpkgs/pull/395556 skipping non binary executables (very discriminatory)
            postFixup = ''
                wrapQtApp "$out/bin/threedont"
            '';
            
            buildInputs = with pkgs; [
              eigen
              qt6.qtbase
            ] ++ lib.optionals stdenv.hostPlatform.isLinux [ qt6.qtwayland.dev libGL ];
            
            dependencies = with pkgs.python3Packages; [
              numpy
              sparqlwrapper
              rdflib
              networkx
              openai
              owlready2
              platformdirs
              nltk
              editdistance
              jarowinkler
            ];
          };
          owlready2 = pkgs.python3Packages.callPackage ({buildPythonPackage, fetchPypi, distutils}:
            buildPythonPackage rec {
              pname = "owlready2";
              version = "0.47";
              src = fetchPypi {
                inherit pname version;
                hash = "sha256-r34dIgXAtYhtLjQ5erjBDKKf9ow9w3AtQzk5Zqx/brA=";
              };
              propagatedBuildInputs = [
                distutils
              ];
            }
          ) {};
        };

        devShells = {
          default = pkgs.mkShell {
            inputsFrom = [ self.packages.${system}.threedont ];
            packages = with pkgs; [
              python3Packages.build
              qt6.qttools
              gdb
              lldb
            ] ++ lib.optionals stdenv.hostPlatform.isLinux [ gammaray ];
            nativeBuildInputs = with pkgs; [
              qt6.wrapQtAppsHook
              makeWrapper
            ];
            # https://discourse.nixos.org/t/python-qt-woes/11808/10
            shellHook = ''
              setQtEnvironment=$(mktemp --suffix .setQtEnvironment.sh)
              # echo "shellHook: setQtEnvironment = $setQtEnvironment"
              makeWrapper "/bin/sh" "$setQtEnvironment" "''${qtWrapperArgs[@]}"
              sed "/^exec/d" -i "$setQtEnvironment"
              source "$setQtEnvironment"
            '';
          };
        };
      });
}
