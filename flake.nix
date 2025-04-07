# nix comment
{
  description = "3dont, ontology pointcloud visualizer";

  inputs.nixpkgs.url = "nixpkgs/nixos-unstable"; # 24.11

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
            
            buildInputs = with pkgs; [
              eigen
              tbb.dev
              qt6.qtbase
            ] ++ lib.optionals stdenv.hostPlatform.isLinux [ qt6.qtwayland libGL ]
            ++ lib.optionals stdenv.hostPlatform.isDarwin [ llvmPackages.openmp ];# darwin.apple_sdk.frameworks.OpenGL ];
            
            dependencies = with pkgs.python3Packages; [
              numpy
              sparqlwrapper
            ];
          };
        };

        apps = {
          python = {
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
              gdb
              lldb
            ];
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
